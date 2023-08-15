import boto3
import os

import json
import datetime
import time


def remove_inactive_context(context_list):
    if not context_list:
        return context_list
    new_context = []
    for context in context_list:
        time_to_live = context.get('timeToLive')
        if  time_to_live and time_to_live.get('turnsToLive') != 0:
            new_context.append(context)
    return new_context

def get_active_contexts(intent_request):
    try:
        return intent_request['sessionState'].get('activeContexts')
    except:
        return []

def get_session_attributes(intent_request):
    try:
        return intent_request['sessionState']['sessionAttributes']
    except:
        return {}


def get_intent(intent_request):
    interpretations = intent_request['interpretations'];
    if len(interpretations) > 0:
        return interpretations[0]['intent']
    else:
        return None;
        
def elicit_intent(active_contexts, session_attributes, elicit_intent, messages):
    active_contexts = remove_inactive_context(active_contexts)
    elicit_intent['state'] = 'Fulfilled'
    
    if not session_attributes:
        session_attributes = {}
    session_attributes['previous_message'] = json.dumps(messages)
    session_attributes['previous_dialog_action_type'] = 'ElicitIntent'
    session_attributes['previous_slot_to_elicit'] = None
    print(elicit_intent)
    print(active_contexts)
    print(session_attributes)
    return {
        'sessionState': {
            'sessionAttributes': session_attributes,
            'activeContexts': active_contexts,
            'dialogAction': {
                'type': 'ElicitIntent'
            },
            "state": "Fulfilled"
        },
        'requestAttributes': {},
        'messages': messages
    }






def validate(slots):

    # valid_cities = ['mumbai','delhi','banglore','hyderabad']
    if not slots['PhoneNumEmp']:
        
        return {
        'isValid': False,
        'violatedSlot': 'PhoneNumEmp',
        
    }
    
    if not slots['FirstName']:
        print("Inside Empty Location")
        return {
        'isValid': False,
        'violatedSlot': 'FirstName',
    }    
    
        

        
    if not slots['job_position']:
        return {
        'isValid': False,
        'violatedSlot': 'job_position',
       
    }
        


    return {'isValid': True}
    
    
    
    
    
def lambda_handler(event, context):
    
    # print(event)
    slots = event['sessionState']['intent']['slots']
    intent = event['sessionState']['intent']['name']
    print(event['invocationSource'])
    print(intent)
    print(slots)
    if intent  == "FallbackIntent": 
       messages  = [{'contentType': 'PlainText', 'content': "please enter a command , I can book you a hotel"}] 
       response = elicit_intent(get_active_contexts(event),get_session_attributes(event),get_intent(event), messages)
       return response
    validation_result = validate(event['sessionState']['intent']['slots'])
    

        
    
    if event['invocationSource'] == 'DialogCodeHook':
        if not validation_result['isValid']:
            
            if 'message' in validation_result:
            
                response = {
                "sessionState": {
                    "dialogAction": {
                        'slotToElicit':validation_result['violatedSlot'],
                        "type": "ElicitSlot"
                    },
                    "intent": {
                        'name':intent,
                        'slots': slots
                        
                        }
                },
                "messages": [
                    {
                        "contentType": "PlainText",
                        "content": validation_result['message']
                    }
                ]
               } 
            else:
                response = {
                "sessionState": {
                    "dialogAction": {
                        'slotToElicit':validation_result['violatedSlot'],
                        "type": "ElicitSlot"
                    },
                    "intent": {
                        'name':intent,
                        'slots': slots
                        
                        }
                }
               } 
    
            return response
           
        else:
            response = {
            "sessionState": {
                "dialogAction": {
                    "type": "Delegate"
                },
                "intent": {
                    'name':intent,
                    'slots': slots
                    
                    }
        
            }
        }
            return response
    
    if event['invocationSource'] == 'FulfillmentCodeHook':
        
        # Add order in Database
        
        interpreted_first_name = event['sessionState']['intent']['slots']['FirstName']['value']['interpretedValue']
        print("Interpreted First Name:", interpreted_first_name)
        interpreted_phone_number = event['sessionState']['intent']['slots']['PhoneNumEmp']['value']['interpretedValue']
        print("Interpreted Phone Number:", interpreted_phone_number)
        interpreted_job_position = event['sessionState']['intent']['slots']['job_position']['value']['interpretedValue']
        print("Interpreted Job Position:", interpreted_job_position)
        dynamodb = boto3.resource("dynamodb")
        table_name = os.environ["TABLE_NAME"]
        table = dynamodb.Table(table_name)
        table.put_item(Item={"PhoneNumEmp": interpreted_phone_number, "interpreted_first_name": interpreted_first_name,"interpreted_job_position": interpreted_job_position })
        response = {
        "sessionState": {
            "dialogAction": {
                "type": "Close"
            },
            "intent": {
                'name':intent,
                'slots': slots,
                'state':'Fulfilled'
                
                }
    
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": "Thanks, I have log your information"
            }
        ]
    }
            
        return response
# code to check the intend 