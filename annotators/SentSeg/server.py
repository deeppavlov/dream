
from flask import Flask, jsonify, request
import sentsegmodel as model
import tensorflow as tf
import json
import uuid
import logging
import requests

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

class pars:
	def __init__(self, dict_properties):
		for k, v in dict_properties.items():
			setattr(self, k, v)

dict_params = json.load(open("config.json"))
params = pars(dict_params)

model = model.model(params)

saver = tf.train.Saver()
sess = tf.Session()
saver.restore(sess, params.model_path)
logger.info("sentseg model is loaded.")


app = Flask(__name__)

@app.route('/sentseg', methods=['POST'])
def respond():
    user_sentences = request.json['sentences']
    session_id = uuid.uuid4().hex

    sentseg_result = []    

    for i, text in enumerate(user_sentences):
        logger.info(f"user text: {text}, session_id: {session_id}")
        sentseg = model.predict(sess, text)
        sentseg_result += [sentseg]                
        logger.info(f"punctuated sent. : {sentseg}")

    return jsonify(sentseg_result)

if __name__ =='__main__':	
	app.run(debug=False, host='0.0.0.0', port=3000)