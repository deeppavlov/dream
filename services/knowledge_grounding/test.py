import requests


def test_knowledge_grounding():
    url = 'http://0.0.0.0:8083/respond'

    topic = "financial endowment"
    knowledge = "<h1> financial endowment </h1> <h2> <anchor> criticisms </anchor> </h2> <p> officials in charge of " \
                "the endowments of some universities have been criticized for ' hoarding ' and reinvesting too much " \
                "of the endowment's income . \ngiven a historical endowment performance of 10 – 11 % , and a payout " \
                "rate of 5 % , around half of the endowment's income is reinvested . \nroughly 3 % of the " \
                "reinvestment is used to keep pace with inflation , leaving an inflation-adjusted 2 % annual " \
                "growth of the endowment . \nof course , many endowments fail to earn 10 – 11 % . \n</p> <p> " \
                "two arguments against inflation-adjusted endowment growth are : </p> <h3> hoarding money </h3> <p> " \
                "large endowments have been criticized for ' hoarding ' money . \nmost philanthropies are required " \
                "by federal law to distribute 5 % of their assets per year , but university endowments are not " \
                "required to spend anything . \nmany universities with very large endowments would require less " \
                "than 5 % to pay full tuition for all their students . \nfor example , it has been estimated that " \
                "if in 2006 all the harvard students had paid the maximum in tuition and fees , it would have " \
                "amounted to less than $ 300 million . \nin 2007 , if harvard <h3> size </h3> <p> financial " \
                "endowments range in size depending on the size of the institution and the level of community " \
                "support . \nat the large end of the spectrum , the total endowment can be over one billion " \
                "dollars at many leading private universities . \nharvard university has the largest endowment " \
                "in the world with $ 37.6 billion in assets as of june 30 , 2015 . \neach university typically " \
                "has numerous endowments , each of which are frequently restricted to funding very specific areas " \
                "of the university . \nthe most common examples are endowed professorships , and endowed " \
                "scholarships or fellowships <h3> socially and environmentally responsible investing </h3> <p> " \
                "many college and university endowments have come under fire in recent years for practices such " \
                "as investing in fossil fuels , ' land grabs ' in poor countries and high-risk , high-return " \
                "investment practices that led to the financial crisis . </p>"
    text = "wow do you know about financial endowment?"
    history = "hello how are you\n fine just got from work \n me too what do you do for living? \n i am a financist"

    request_data = {'batch': [{'topic': topic, 'knowledge': knowledge, 'text': text, 'history': history}]}
    result = requests.post(url, json=request_data).json()[0]
    assert result != '', f'Got empty string as a result'
    print('Got\n{}\nSuccess'.format(result))


if __name__ == '__main__':
    test_knowledge_grounding()
