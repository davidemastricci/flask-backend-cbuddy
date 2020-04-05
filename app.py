#modified
# import flask dependencies
from flask import Flask, request, make_response, jsonify
from today_statistics import get_today_national_stats, get_today_regional_stats, get_today_province_stats

# initialize the flask app
app = Flask(__name__)

# constants
GET_NATIONAL_STATS = "lookup_today_statisics"
GET_REGIONAL_STATS = "lookup_today_regional_statisics"
GET_PROVINCE_STATS = ""


# default route
@app.route('/')
def index():
    return 'Hello World!'


# function for responses
def results():
    # build a request object
    req = request.get_json(force=True)

    # fetch action from json
    action = req.get('queryResult').get('action')
    params = req.get('queryResult').get("parameters")

    method_to_call = __actions__(action)

    # get data
    googleResponse, facebookResponse = method_to_call(params)

    # return a fulfillment response
    return create_simple_response(googleResponse, facebookResponse)


def create_simple_response(googleAssistanResponse, facebookResponse):
    """
    Create a dictionary for a simple response
    :param data: dataframe that contain data to be explained
    :return: a dictionary that can be jsonfied
    """

    return \
        {
            "payload": {
                "google": {
                    "expectUserResponse": True,
                    "richResponse": {
                        "items": [
                            {
                                "simpleResponse": {
                                    "textToSpeech": googleAssistanResponse[0],
                                    "displayText": googleAssistanResponse[1]
                                }
                            }
                        ]
                    }
                }
            },
            "fulfillmentText": googleAssistanResponse[1]
        }


def lista():
    return ""


def __actions__(action):
    """
    Check which action has to be called.
    :param action: the action requested
    :return: the function that must be called
    """
    switcher = {  # Create a map between action from dialogflow and function implemented here
        GET_NATIONAL_STATS: get_today_national_stats,
        GET_REGIONAL_STATS: get_today_regional_stats,
        GET_PROVINCE_STATS: get_today_province_stats,
        3: 'Wednesday',
        4: 'Thursday',
        5: 'Friday',
        6: 'Saturday'
    }
    return switcher.get(action, "Invalid day of week")


# create a route for webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    return make_response(jsonify(results()))


# run the app
if __name__ == '__main__':
    app.run()
