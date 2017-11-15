# -*- coding: utf-8 -*-
import os
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import pandas as pd
from haversine import haversine
from math import radians
import ast

app = Flask(__name__)

global bot
bot = telegram.Bot(token=[TELEGRAM_TOKEN])

TOKEN = [TELEGRAM_TOKEN]

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def start(bot, update):
    """ When user presses /start, prompts user for location or postal code with buttons"""

    location_keyboard = telegram.KeyboardButton(text="Send current location", request_location=True)
    postal_code = telegram.KeyboardButton(text="Input a postal code")
    custom_keyboard = [[location_keyboard, postal_code]]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard, one_time_keyboard=True, resize_keyboard=True)
    bot.send_message(chat_id=update.message.chat_id, text="Hello hello! You want to send me your current location or input a postal code?", reply_markup=reply_markup)


def location(bot, update):
    """ If user sends location """

    bot.send_message(chat_id=update.message.chat_id, text="OK you wait ah...")
    latitude = update.message.location.latitude 
    longitude = update.message.location.longitude 
    bot.send_message(chat_id=update.message.chat_id, text="Just let you know for fun lol - your latitude is {0}, and your longitude is {1}".format(latitude,longitude))
    try:
        # Read carpark csv as dataframe
        df = pd.read_csv('Parking_withcoords.csv')
    
        # Calculate distance between each carpark and postal code and append it to dataframe
        distance = []
        for coord in df['Coord_rad']:  
            carpark = haversine((radians(latitude),radians(longitude)), ast.literal_eval(coord)) #converts string to tuple
            distance.append(carpark)
        df['Distance_km'] = distance

        # Sort in ascending order and extract top 5
        top_five = df.sort_values('Distance_km').head(5)

        for row in top_five['Info']:
            bot.send_message(chat_id=update.message.chat_id, parse_mode='HTML', text=row)

        bot.send_message(chat_id=update.message.chat_id, text="Fast hor! If you want to check other places, type /start again ok :P")
    except:
        bot.send_message(chat_id=update.message.chat_id, text="Jialat liao got error...try again with /start and then use the postal code method can? Paiseh!")
    



def respond(bot, update):
    """ If user sends any text response """

    def postalcode(userinput):
        front_url = "https://maps.googleapis.com/maps/api/geocode/json?address="
        end_url = "&components=country:SG&key=AIzaSyB-lR8VoOizlVvhK-p8CR6Lol-wb2RgSM0"
        url = front_url + str(userinput) + end_url
        address = pd.read_json(url)
        p_lat = radians(address['results'][0]['geometry']['location']['lat'])
        p_lng = radians(address['results'][0]['geometry']['location']['lng'])
        return (p_lat, p_lng)   

    def error_msg(): 
        location_keyboard = telegram.KeyboardButton(text="Send current location", request_location=True)
        postal_code = telegram.KeyboardButton(text="Input a postal code")
        custom_keyboard = [[location_keyboard, postal_code]]
        reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard, one_time_keyboard=True, resize_keyboard=True)
        bot.send_message(chat_id=update.message.chat_id, text="Cannot leh. You want try again?", reply_markup=reply_markup)
    
    if update.message.text == 'Input a postal code':
        bot.send_message(chat_id=update.message.chat_id, text="Ok please give me a postal code (6 digits only hor)")
    elif len(update.message.text) == 6:
        bot.send_message(chat_id=update.message.chat_id, text="You wait ah I check")
        try:
            # Check if Google Maps API is able to get geo coords from the 6 digits
            postal = postalcode(int(update.message.text))
            
            # Read carpark csv as dataframe
            df = pd.read_csv('Parking_withcoords.csv')

            # Calculate distance between each carpark and postal code and append it to dataframe
            distance = []
            for coord in df['Coord_rad']:  
                carpark = haversine(postal, ast.literal_eval(coord)) #converts string to tuple
                distance.append(carpark)
            df['Distance_km'] = distance

            # Sort in ascending order and extract top 5
            top_five = df.sort_values('Distance_km').head(5)
            
            for row in top_five['Info']:
                bot.send_message(chat_id=update.message.chat_id, parse_mode='HTML', text=row)
                
            bot.send_message(chat_id=update.message.chat_id, text="Fast hor! If you want to check other places, type /start again ok :P")
        
        except:
            error_msg()
    else:
        error_msg()



def help(bot, update):
    """ If user sends /help command """
    bot.send_message(chat_id=update.message.chat_id, text="Type /start to start LOL")

def unknown(bot, update):
    """ If user sends unknown command """
    bot.send_message(chat_id=update.message.chat_id, text="Sorry leh, I don't know that command. If you dunno got what command, just type / then everything will come out")

def error(bot, update, error):
    """ Log Errors"""
    logger.warning('Update "%s" caused error "%s"' % (update, error))

def main():
    """ This is where the bot starts from! """

    # Create the EventHandler and pass it your bot's token.
    telegram = [TELEGRAM_TOKEN] # saved on heroku's config vars

    bot = telegram.Bot(token=telegram)
    updater = Updater(token=telegram)
    j = updater.job_queue

    # Get the dispatcher to register handlers
    dispatch = updater.dispatcher

    # on different commands - answer in Telegram
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    location_handler = MessageHandler(Filters.location, location)
    dispatcher.add_handler(location_handler)

    respond_handler = MessageHandler(Filters.text, respond)
    dispatcher.add_handler(respond_handler)

    help_handler = CommandHandler('help', help)
    dispatcher.add_handler(help_handler)

    unknown_handler = MessageHandler(Filters.command, unknown)
    dispatcher.add_handler(unknown_handler)

    # create jobs
    # job_minute = Job(monitor_promo, 900)
    # j.put(job_minute, next_t=60)

    j.run_repeating(monitor_promo, 600, 15)
    j.run_repeating(monitor_train, 300, 60)

    # log all errors
    dispatch.add_error_handler(error)

    # Start the Bot
    """
    #DEV
    updater.start_polling()
    # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
    """

    #PROD
    port_number = int(os.environ.get('PORT', '5000'))
    updater.start_webhook(listen="0.0.0.0",
                          port=port_number,
                          url_path=telegram)
    updater.bot.setWebhook("https://dashproject.herokuapp.com/" + telegram)
    updater.idle()

if __name__ == '__main__':
    main()