# AIConnection.py
# AI SQ Grader - AI connection                                  (Fox)
#
# Sends one request to an OpenAI-compatible /chat/completions service (OpenAI, DeepSeek or
# any service with the same interface) and returns one AIResponse record. A request can
# include images (photos of answers, scanned pages), which are sent as base64 data URLs;
# this needs a model that accepts images, e.g. gpt-4o-mini.
# Used by the Document Processing, Grading and Feedback, and Correction modules, and by
# the main module to test the connection.
#
# Acknowledgement: the record types in SQRecords.py were agreed by the whole group.

import base64              # turns image bytes into text so they can be sent in a JSON request
import json                # converts between JSON text and Python lists / dictionaries
import os                  # os.path finds the size and extension of an image file
import time                # waits before a failed request is tried again
import urllib.error
import urllib.request      # sends the request to the AI service

import SQRecords

# CONSTANT
ProviderNames = ["OpenAI", "DeepSeek"]
ProviderURLs = ["https://api.openai.com/v1", "https://api.deepseek.com/v1"]
MaxRequestAttempts = 3
RequestTimeout = 120                   # seconds; reading images can take a while
RetryStatusCodes = [408, 409, 429, 500, 502, 503, 504]
ImageTypes = [".png", ".jpg", ".jpeg", ".webp"]
ImageMimeTypes = ["image/png", "image/jpeg", "image/jpeg", "image/webp"]
MaxImageBytes = 15000000               # larger photos are refused by most AI services


def IsInList(Item, ItemList):
    # Linear search: TRUE if Item is in ItemList.
    # DECLARE Index : INTEGER
    for Index in range(0, len(ItemList)):
        if ItemList[Index] == Item:
            return True
    return False


def IsOnline(Settings):
    # TRUE if a real AI service (not the offline demo marker) is chosen.
    return Settings.Provider != SQRecords.OfflineProvider


def GetBaseURL(Provider):
    # Returns the web address of the provider's API, or "" if the provider is unknown.
    # A provider written as a URL (https://...) is used as it is.
    # DECLARE Index : INTEGER
    if Provider[0:8] == "https://" or Provider[0:7] == "http://":
        while len(Provider) > 0 and Provider[len(Provider) - 1:] == "/":
            Provider = Provider[0:len(Provider) - 1]
        return Provider
    for Index in range(0, len(ProviderNames)):
        if ProviderNames[Index].upper() == Provider.upper():
            return ProviderURLs[Index]
    return ""


def BytesToImageURL(ImageBytes, MimeType):
    # data URL: "data:image/png;base64," followed by the image as base64 text
    return "data:" + MimeType + ";base64," + base64.b64encode(ImageBytes).decode("ascii")


def MakeImageURL(FileName):
    # Reads an image file and returns it as a data URL, or "" (with a message) if it
    # cannot be used.
    # DECLARE Extension, MimeType : STRING
    # DECLARE Index : INTEGER
    # DECLARE ImageBytes : BYTES
    Extension = os.path.splitext(FileName)[1].lower()
    MimeType = ""
    for Index in range(0, len(ImageTypes)):
        if ImageTypes[Index] == Extension:
            MimeType = ImageMimeTypes[Index]
    if MimeType == "":
        print("Not an image file that can be sent:", os.path.basename(FileName))
        return ""
    try:
        if os.path.getsize(FileName) > MaxImageBytes:
            print("The image", os.path.basename(FileName), "is too large (over 15 MB). Use a smaller photo.")
            return ""
        File = open(FileName, "rb")
        ImageBytes = File.read()
        File.close()
    except IOError:
        print("The image", os.path.basename(FileName), "could not be read.")
        return ""
    return BytesToImageURL(ImageBytes, MimeType)


def GetReplyContent(ReplyData):
    # Takes the reply text out of a /chat/completions response: choices[0].message.content
    # Returns "" if the response does not have that shape.
    try:
        Data = json.loads(ReplyData)
        return str(Data["choices"][0]["message"]["content"])
    except (ValueError, KeyError, IndexError, TypeError):
        return ""


def ExtractJsonText(ReplyText):
    # Returns the text from the first "{" to the last "}", which removes any ``` fences or
    # words that the AI wrote around the JSON. Returns "" if there are no braces.
    # DECLARE Start, Finish, Index : INTEGER
    Start = -1
    Finish = -1
    for Index in range(0, len(ReplyText)):
        if ReplyText[Index] == "{":
            if Start == -1:
                Start = Index
        elif ReplyText[Index] == "}":
            Finish = Index
    if Start == -1 or Finish < Start:
        return ""
    return ReplyText[Start:Finish + 1]


def GetJsonList(Data, Key):
    # Returns Data[Key] if Data is a dictionary and Data[Key] is a list, otherwise [].
    # (json.loads returns a dictionary for a JSON object; .get gives None for a missing key)
    if type(Data) == dict and type(Data.get(Key)) == list:
        return Data[Key]
    return []


def ReadJsonReply(Response):
    # Returns the JSON object in a successful AIResponse as a dictionary, or None.
    # DECLARE Data : dictionary
    if Response.Success == False:
        return None
    try:
        Data = json.loads(ExtractJsonText(Response.ReplyText))
    except ValueError:
        return None
    if type(Data) != dict:
        return None
    return Data


def SendChatRequest(PromptText, ImageURLs, Settings):
    # Sends PromptText (and any images) to the AI service in AISettings and returns one
    # AIResponse record. A request that fails with a temporary error is tried up to
    # MaxRequestAttempts times.
    # DECLARE Response : AIResponse
    # DECLARE BaseURL, ReplyData : STRING
    # DECLARE Content : ARRAY   (text part, then one part for each image)
    # DECLARE Attempt, Index : INTEGER
    # DECLARE Finished : BOOLEAN
    Response = SQRecords.AIResponse()
    if IsOnline(Settings) == False:
        Response.ErrorMessage = "No AI service is chosen (the offline demo marker cannot read documents)."
        return Response
    BaseURL = GetBaseURL(Settings.Provider)
    if BaseURL == "":
        Response.ErrorMessage = "Unknown AI provider: " + Settings.Provider
        return Response
    if Settings.APIKey == "" or Settings.ModelName == "":
        Response.ErrorMessage = "The API key or model name is missing."
        return Response

    if len(ImageURLs) == 0:
        Content = PromptText
    else:
        Content = [{"type": "text", "text": PromptText}]
        for Index in range(0, len(ImageURLs)):
            Content.append({"type": "image_url", "image_url": {"url": ImageURLs[Index], "detail": "high"}})
    RequestBody = {"model": Settings.ModelName,
                   "temperature": 0,
                   "response_format": {"type": "json_object"},
                   "messages": [{"role": "user", "content": Content}]}
    RequestData = json.dumps(RequestBody).encode("utf-8")
    Attempt = 0
    Finished = False
    while Finished == False:
        Attempt = Attempt + 1
        try:
            Request = urllib.request.Request(BaseURL + "/chat/completions", data=RequestData, method="POST")
            Request.add_header("Content-Type", "application/json")
            Request.add_header("Authorization", "Bearer " + Settings.APIKey)
            Reply = urllib.request.urlopen(Request, timeout=RequestTimeout)
            ReplyData = Reply.read().decode("utf-8")
            Reply.close()
            Response.ReplyText = GetReplyContent(ReplyData)
            if Response.ReplyText == "":
                Response.ErrorMessage = "The AI service sent a reply with no content."
            else:
                Response.Success = True
                Response.ErrorMessage = ""
            Finished = True
        except urllib.error.HTTPError as Error:
            Response.ErrorMessage = "The AI service returned HTTP error " + str(Error.code)
            if Error.code == 400 and len(ImageURLs) > 0:
                Response.ErrorMessage = Response.ErrorMessage + " (the model may not accept images)"
            if IsInList(Error.code, RetryStatusCodes) == False or Attempt >= MaxRequestAttempts:
                Finished = True
            else:
                time.sleep(2 * Attempt)
        except (urllib.error.URLError, OSError):
            Response.ErrorMessage = "The AI service could not be reached (network error or time-out)."
            if Attempt >= MaxRequestAttempts:
                Finished = True
            else:
                time.sleep(2 * Attempt)
    return Response


def TestConnection(Settings):
    # Sends a very small request and reports whether the AI service answers correctly.
    # Returns TRUE if the connection works.
    # DECLARE Response : AIResponse
    # DECLARE Data : dictionary
    if IsOnline(Settings) == False:
        print("The offline demo marker is chosen, so there is no AI service to test.")
        return False
    print("Testing", Settings.Provider, "with the model", Settings.ModelName, "...")
    Response = SendChatRequest('Reply with this JSON only: {"ok": true}', [], Settings)
    Data = ReadJsonReply(Response)
    if Data is None:
        if Response.Success == False:
            print("The test failed:", Response.ErrorMessage)
        else:
            print("The service answered, but not with JSON. Choose another model.")
        return False
    print("The AI service is working.")
    return True


# main - tests the connection given by the environment variables SQ_PROVIDER, SQ_MODEL, SQ_API_KEY
if __name__ == "__main__":
    TestSettings = SQRecords.AISettings()
    TestSettings.Provider = os.environ.get("SQ_PROVIDER", SQRecords.OfflineProvider)
    TestSettings.ModelName = os.environ.get("SQ_MODEL", "gpt-4o-mini")
    TestSettings.APIKey = os.environ.get("SQ_API_KEY", "")
    print("Working:", TestConnection(TestSettings))
