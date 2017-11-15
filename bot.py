# -*- coding: utf-8 -*-
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import pandas as pd
from haversine import haversine
from math import radians
import ast

# Prompts user for location or postal code with buttons
def start(bot, update):
    location_keyboard = telegram.KeyboardButton(text="Send current location", request_location=True)
    postal_code = telegram.KeyboardButton(text="Input a postal code")
    custom_keyboard = [[location_keyboard, postal_code]]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard, one_time_keyboard=True, resize_keyboard=True)
    bot.send_message(chat_id=update.message.chat_id, text="Hello hello! You want to send me your current location or input a postal code?", reply_markup=reply_markup)


# Function when user sends location
def location(bot, update):
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


# Function to scan user's text response
def respond(bot, update):
    def postalcode(userinput):
        front_url = "https://maps.googleapis.com/maps/api/geocode/json?address="
        end_url = "&components=country:SG&key=AIzaSyB-lR8VoOizlVvhK-p8CR6Lol-wb2RgSM0"
        url = front_url + str(userinput) + end_url
        address = pd.read_json(url)
        p_lat = radians(address['results'][0]['geometry']['location']['lat'])
        p_lng = radians(address['results'][0]['geometry']['location']['lng'])
        return (p_lat, p_lng)   

    def error(): 
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
            error()
    else:
        error()




def help(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Type /start to start LOL")

help_handler = CommandHandler('help', help)
dispatcher.add_handler(help_handler)

def unknown(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Sorry leh, I don't know that command. If you dunno got what command, just type / then everything will come out")

unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)
    

def main():
    while True:
        # Enable logging
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

        # Set up bot, updater, dispatcher
        bot = telegram.Bot(token='[TELEGRAM_TOKEN]')
        updater = Updater(token='[TELEGRAM_TOKEN]')
        dispatcher = updater.dispatcher

        # /start
        start_handler = CommandHandler('start', start)
        dispatcher.add_handler(start_handler)

        # If location is sent
        location_handler = MessageHandler(Filters.location, location)
        dispatcher.add_handler(location_handler)

        # If there is a response
        respond_handler = MessageHandler(Filters.text, respond)
        dispatcher.add_handler(respond_handler)

        # Start bot
        updater.start_polling()


if __name__ == '__main__':
    main()