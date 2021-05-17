from rasa_nlu import config
from rasa_nlu.training_data  import load_data
from rasa_nlu.config import RasaNLUModelConfig
from rasa_nlu.model import Trainer, Metadata, Interpreter

import json
import os # use in join path
import csv


# MANIPULATE FILE ##################
def read_json_file(file_directory):
    with open(file_directory,mode='r') as json_file:
        data_set = json.load(json_file)
        return data_set

def save_json_file(json_data,file_directory):
    with open(file_directory, mode='w') as json_file:
        json.dump(json_data, json_file)

def save_csv_file(dictionary_data,CSVname):
    list_data = []
    list_data.append(['Name','Intent','Confident score','Answer'])
    for name in dictionary_data:
        list_data.append([name,dictionary_data[name]['intent'],dictionary_data[name]['percentage'],dictionary_data[name]['answer']])
    #print (list_data)
    with open(CSVname+'.csv', mode='w',newline='') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerows(list_data)
    csvFile.close()
    return 'Export to csv file success'

# ADD NEW INTENT IN DATASET ##################
def combine_text_intent(text,intent):
    new_sample = {}
    new_sample["text"] = text.capitalize() 
        #turn string to sentence case letter
    new_sample["intent"]=  intent.lower()  
        #turn string to lower case letter
    new_sample["entities"]=[]
    #print (new_sample)
    return new_sample

def add_dataset(text,intent,file_directory):
    existing_data_set = read_json_file(file_directory) #read dataset json file
    for id in existing_data_set:
        #print(existing_data_set[id]['common_examples'])
        existing_data_set[id]['common_examples'].append(combine_text_intent(text,intent)) #append new text and intent inside
        #print (existing_data_set)
        save_json_file(existing_data_set,file_directory)    
            #write new_data_set in test_dataset.json
            #write new data set in the same file
    #print (type(existing_data_set)) #identitfy type of object
    return "function add_dataset success"

# TRAIN MODEL ##################
def train_model (dataset_directory,model_name,model_name_directory): #need to told model name directory
    train_data = load_data(dataset_directory) #load data file and assign in train_data
    trainer = Trainer(config.load("config_spacy.yaml")) #load config file
    trainer.train(train_data) # Training Data
    trainer.persist(model_name_directory, fixed_model_name = model_name) 
        # Returns the directory the model is stored in (Creat a folder to store model in) and you can fixed the model name
    # metadata = read_json_file('metadata.json')
    # metadata['model_name'] = model_name
    # save_json_file(metadata,'metadata.json') 
    return "function train_model success"

# ADD NEW ANSWER IN RAW DATA ################## 
def add_new_response(new_name,new_answer,existing_response):
    new_response = {}
    number = len(existing_response['raw_data'])
    #print (number)
    new_response[str(number+1)] = {'name':new_name,'answer':new_answer}
    for id in new_response:
        existing_response['raw_data'][id]=new_response[id]
    return existing_response

def add_answer(new_name,new_answer,file_directory):
    existing_response = read_json_file(file_directory)
    all_response = add_new_response(new_name,new_answer,existing_response)
    save_json_file(all_response,file_directory)
    return "function add_answer success"

# PREDICT MODEL ##################
def prediction_with_model(raw_data_directory,model_name_directory): #need to told dynamic model folder
    result_data = {'predict_data':{}}
    raw_data = (read_json_file(raw_data_directory))['raw_data']
    #model_name = (read_json_file(metadata_directory))['model_name']
    #print (raw_data)
    #print (model_name)

    for id in raw_data:
        #path = os.path.join(model_name, "default", model_name)
        path = model_name_directory
        interpreter = Interpreter.load(path) 
        prediction_raw = (interpreter.parse(str(raw_data[id]['answer'])))
        #print (prediction_raw)
        if (prediction_raw['intent']['confidence']>= 0.3): #pass the confidence threshold
            intent_name = prediction_raw['intent']['name']
            confidence_in_percent = str(100*(prediction_raw['intent']['confidence'])//1)+'%'
            answer = str(raw_data[id]['answer'])
            name = str(raw_data[id]['name'])
            #print (intent_name)
            #print (confidence_in_percent)
            result_data['predict_data'][id] = {'name':name,'percentage':confidence_in_percent,'answer':answer,'intent':intent_name}
        else:   #fail the confidence threshold
            answer = str(raw_data[id]['answer'])
            name = str(raw_data[id]['name'])
            result_data['predict_data'][id] = {'name':name,'percentage':'0%','answer':answer,'intent':'unknow intent'}
    return (result_data) 

def predict_model(raw_data_directory,model_name_directory,predict_data_directory):
    predict_data = prediction_with_model(raw_data_directory,model_name_directory)
    save_json_file(predict_data,predict_data_directory)
    return "function predict_model success"

# EXPORT TO CSV FILE ##################
def export_csv_file(predict_data_directory, csv_directory):
    predict_data = (read_json_file(predict_data_directory))['predict_data']
    list_data = []
    list_data.append(['Id','Name','Intent','Confident score','Answer'])
    for id in predict_data:
        list_data.append([id,predict_data[id]['name'], predict_data[id]['intent'], predict_data[id]['percentage'], predict_data[id]['answer']])
    #print (list_data)
    with open(csv_directory, mode='w',newline='') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerows(list_data)
    csvFile.close()
    return 'Export to csv file success'

#train_model ('rasa_dataset.json','model_name')
#predict_model('raw_data.json','metadata.json','predict_data.json')