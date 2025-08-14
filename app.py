from flask import Flask, request, jsonify
from src.model.twitter.client import Twitter

app = Flask(__name__)

@app.route('/tweet', methods=['POST'])
def create_tweet():
    data = request.json
    text = data.get('text', '')
    media = data.get('media', None)  # Base64 изображение
    
    twitter_client = Twitter(auth_token=data.get('auth_token'))
    response = twitter_client.tweet(text=text, media_base64=media)
    
    return jsonify({'success': response})

if __name__ == '__main__':
    app.run(debug=True)