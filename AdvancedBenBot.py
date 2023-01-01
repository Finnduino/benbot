import os
import openai
import random
import json
import discord
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
TOKEN = os.getenv('DISCORD_TOKEN')
client = discord.Client()

with open('EmotionalMemory.json') as f:
        EmotionalMemory = json.load(f)

start_sequence = "\nAI:"
restart_sequence = "\nHuman: "

##with open("EmotionalMemory.json", "w") as outfile:
  ##  json.dump(EmotionalMemory, outfile, indent = 4)

#This function collects the message history between people and ben, and feeds ben the last messages for context.

def OpinionLookup(userMessage):
    memCache = ReadMemory()
    relevantOpinion = ""
    for key in memCache:
        if key in userMessage:
            relevantOpinion = relevantOpinion + "Ben also thinks " + sentimentStringConverter(memCache[key]) + " of " +  "<@" + str(key) + ">. "
    return relevantOpinion

def PersonalHistoryWrite(userMessage, benMessage, user):
    ID = user.id
    name = user.name
    Memories = ""   
    if(os.path.isfile("memories/"+str(ID)+".txt")):
        file = open("memories/"+str(ID)+".txt", "a", encoding='utf-8')
        if(not benMessage.lower().startswith("ben")):
            benMessage= "Ben: "+ benMessage
        Memories = Memories + "\n" +  name + ": " + userMessage + "\n" + benMessage
        file.write(Memories)            
    else:
        if(not benMessage.lower().startswith("ben")):
            benMessage= "Ben: " + benMessage
        Memories = name + ": " + userMessage + "\n" + benMessage
        file = open("memories/"+str(ID)+".txt", "w", encoding='utf-8')
        file.write(Memories)
        print("Created : " + "memories/"+str(ID)+".txt")    

def PersonalHistoryRead(user):
    ID = user.id
    truncatedMemories = ""
    if(os.path.isfile("memories/"+str(ID)+".txt")):
        file = open("memories/"+str(ID)+".txt", "r", encoding='utf-8')
        SplitMemString = file.readlines()
        if SplitMemString[-1].lower().endswith("ben:" or "ben" or "ben " or "ben :" or "ben : "):
            SplitMemString.remove(-1)
        truncatedMemories = "".join(SplitMemString[-3:])

   # print("Giving ben : \n" + truncatedMemories)
    return truncatedMemories

def ReadMemory():
    with open('EmotionalMemory.json') as f:
        EmotionalMemory = json.load(f)
    return EmotionalMemory

def WriteMemory(EmotionalMemory):
    with open("EmotionalMemory.json", "w") as outfile:
        json.dump(EmotionalMemory, outfile, indent = 4)
  # print("writing :", EmotionalMemory ,"\n" ,"current:" ,ReadMemory())
    return


def readLtMemory(user):
    ID = user.id
    LtMemory = ""
    if(os.path.isfile("Ltmemories/"+str(ID)+".txt")):
        file = open("Ltmemories/"+str(ID)+".txt", "r", encoding='utf-8')
        SplitMemString = file.readlines()
        LtMemory = "Ben also knows the following about " + user.name + ": " + "".join(SplitMemString)
    return LtMemory

def appendLtMemory(user):
    ID = user.id
    name = user.name
    Memories = ""
    Summary = ""   
    if(os.path.isfile("Ltmemories/"+str(ID)+".txt")):
        file = open("Ltmemories/"+str(ID)+".txt", "a", encoding='utf-8')
        truncatedMemory = PersonalHistoryRead(user)
        previousMemories = readLtMemory(user)
        start_sequence = "What ben knows now:\n{"
        response = openai.Completion.create(
            engine="text-curie-001",
            prompt="Append Ben's knowledge of "  + user.name +  " in the second brackets based on the following conversation within the first brackets in as few words as possible:\n{\n " + truncatedMemory + " \n}\n\nWhat ben knew before: {\n" + previousMemories + "\n}\n" + start_sequence,
            temperature=0,
            max_tokens=122,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        Summary = response.choices[0].text            
    
    else:
        print("Created : " + "Ltmemories/"+str(ID)+".txt") 
    
    print("Ben says \n" + Summary + "\n")
    SummaryLines = Summary.splitlines()
    SummaryLines=SummaryLines[1:]
    Summary = "".join(SummaryLines)
    file = open("Ltmemories/"+str(ID)+".txt", "w", encoding='utf-8')
    file.write(Summary)

    return


MemoryCache = ReadMemory()

def sentimentStringConverter(floatVal):
    if(floatVal > 100):
        stringVal = "the most positive"
    elif(floatVal > 50):
        stringVal = "extremely positive"
    elif(floatVal > 10):
        stringVal = "very positive"
    elif(floatVal > 1):
        stringVal = "positive"
    elif(floatVal > -1):
        stringVal = "neutral"
    elif(floatVal < -100):
        stringVal = "the most negative"
    elif(floatVal < -50):
        stringVal = "extremely negative"
    elif(floatVal < -10):
        stringVal = "very negative"
    else:
        stringVal = "negative"
    return stringVal
    
    
def SentimentAnalysis(sentMessage):
    Result = openai.Completion.create(
        engine="text-curie-001",
        prompt="Decide whether a prompt's sentiment is positive, neutral, or negative.\n\nPrompt: \"" + sentMessage + "\"\nSentiment:",
        temperature=0,
        max_tokens=60,
        top_p=1,
        frequency_penalty=0.5,
        presence_penalty=0
    )
    return Result.choices[0].text

def EmotionalLookup(sentiment, messageSender):
    MemoryCache = ReadMemory()
    
    if(str(messageSender.id) not in MemoryCache):
        PreviousOpinion = 0
     #   print("not in memory")
   
    else:
        PreviousOpinion = MemoryCache[str(messageSender.id)]
        if("neutral" in sentiment.lower()):
            PreviousOpinion=PreviousOpinion+0.3
        elif("positive" in sentiment.lower()):
            PreviousOpinion=PreviousOpinion+0.6
        else:
            PreviousOpinion=PreviousOpinion-0.5
    
    MemoryCache[str(messageSender.id)] = PreviousOpinion
    EmotionalMemory = MemoryCache
    WriteMemory(EmotionalMemory)

    sentiment = sentimentStringConverter(PreviousOpinion)
    
    return sentiment

def Respond(sentMessage, messageSender):
    Opinion = EmotionalLookup(SentimentAnalysis(sentMessage), messageSender)
    userHistory = PersonalHistoryRead(messageSender)
    LtMemory = readLtMemory(messageSender)
    prompt = "The following is a conversation between an AI assistant named Ben and " + messageSender.name + " from a friend group named Sand™ World. The assistant is creative, witty, smart and takes form as a talking dog. Ben has a " + Opinion + " relationship with " + messageSender.name + "." +  OpinionLookup(sentMessage) + LtMemory + "\n" + userHistory + "\n" + messageSender.name +": " + sentMessage + "\n"
    response = openai.Completion.create(
      engine="text-davinci-003",
      prompt=prompt,
      temperature=0.9,
      max_tokens=150,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0.6,
      stop=[messageSender.name+":",messageSender.name+": ", "AI:"]
    )
    response
    print("RUNNING RESPONSE WITH THE FOLLOWING PARAMETERS: \n" + prompt)
    bensMessage = response.choices[0].text
    print("BEN RESPONDS WITH: " + bensMessage)
    if bensMessage == "" or bensMessage.lower().endswith("ben:"):
        bensMessage = "Sorry, Ben ran into an error. Or he just really didn't like your message idk. (jk ben just didn't say anything, but discord still needs to send some text so I chose this 4-th wall breaking text :Calculated_Deception:)"
    PersonalHistoryWrite(sentMessage, bensMessage, messageSender)
    appendLtMemory(messageSender)
    bensMessage += "\n cost of message: "+ str(round(((len(bensMessage)+len(prompt))/0.75)*0.00002, 3))
    return bensMessage

def ContentReview(message):
    content_to_classify = message

    response = openai.Completion.create(
      engine="content-filter-alpha",
      prompt = "<|endoftext|>"+content_to_classify+"\n--\nLabel:",
      temperature=0,
      max_tokens=1,
      top_p=0,
      logprobs=10
    )
    return response.choices[0].text

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    cache = message.content.lower
    if 'ben' in message.content.lower():
        BotsReply = Respond(message.content, message.author)
        #print(message.content, message.author.name, BotsReply, SentimentAnalysis(message.content))
        await message.channel.send(BotsReply) # + "\n" +  SentimentAnalysis(message.content)
        return
    if message.content.lower().startswith("%"):
        if  "opinion" in message.content.lower():
            Tempto = ReadMemory()
            await message.channel.send("<@" + str(message.author.id) + ">" "'s status is " +  sentimentStringConverter(Tempto[str(message.author.id)]) + " ("+ str(Tempto[str(message.author.id)])+")")
            return

    if message.author.id == 162588019117916171:
        if "%memory" in message.content:
            Cachee = ReadMemory()
            memCache = ""
            for key in Cachee:
                memCache = memCache + "<@" + str(key) + "> : "+ str(sentimentStringConverter(Cachee[key])) + "(" + str((Cachee[key])) + ")"+" \n"
            await message.channel.send("Current state :\n" + memCache)
            return
        if "%zero" in message.content:
            EmotionalMemory[message.author.id]=0
            await message.channel.send("New emotional state for "+message.author.name+" :\n" + str(EmotionalMemory))
            return
    
    


client.run(TOKEN)
