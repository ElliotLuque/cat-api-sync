import os
import requests
from pymongo import MongoClient

# Secrets
API_KEY = os.environ['API_KEY']
CONNECT_STRING = os.environ['CONNECT_STRING']

# MongoDB Client
client = MongoClient(CONNECT_STRING)
db = client.cat_api
collection = db.cats

# Request base data
authHeaders = {"Accept": "application/json", "x-api-key": API_KEY}
baseURL = "https://api.thecatapi.com/v1"

# Generate Cat Object
def createCatObject(catId):

    print("CAT " + catId)
    # GET cat data from API
    cat = requests.get(baseURL + "/breeds/" + catId).json()
    if cat["reference_image_id"] is None:
        print("FAILING")
    catReferenceImage = requests.get(baseURL + "/images/" + cat["reference_image_id"] +  "?size=med").json()
    catImages = requests.get(baseURL + "/images/search?size=med&order=DESC&limit=8&include_breeds=false&breed_ids=" + catId, headers = authHeaders).json()
                                        
    # Fill images array
    imagesArray = []
    for image in catImages:
        imagesArray.append(image["url"])

    # Cat attributes
    catObject = {
        "_id": cat["id"],
        "name": cat["name"],
        "temperament": cat["temperament"],
        "origin": cat["origin"],
        "description": cat["description"],
        "reference_image": catReferenceImage["url"],
        "lifespan": cat["life_span"] + " years",
        "adaptability": cat["adaptability"],
        "affection_level": cat["affection_level"],
        "child_friendly": cat["child_friendly"],
        "grooming": cat["grooming"],
        "intelligence": cat["intelligence"],
        "health_issues": cat["health_issues"],
        "social_needs": cat["social_needs"],
        "stranger_friendly": cat["stranger_friendly"],
        "images": imagesArray
    }

    return catObject

# API Sync
catAPI = requests.get(baseURL + "/breeds").json()
listCatsToInsert = []

for breed in catAPI:
    # Check only cats with images
    if "reference_image_id" in breed:

        # Get images from API"s breeds
        catAPIImages = requests.get(baseURL + "/images/search?size=med&order=DESC&limit=8&include_breeds=false&breed_ids=" + breed["id"], headers = authHeaders).json()
        
        # Try to find cat in MongoDB
        cat = collection.find_one({"_id": breed["id"]})

        # If cat doesn"t exist in MongoDB
        if cat is None:
            print("new cat: " + breed["id"])
            # Add to list to insert
            listCatsToInsert.append(createCatObject(breed["id"]))
        # If cat exists
        else:
            # Cat from API
            _apiImages = []
            for apiImage in catAPIImages:
                _apiImages.append(apiImage['url'])

            # Cat from MongoDB
            _catImages = []
            for mongoImage in cat["images"]:
                _catImages.append(mongoImage)

            # Check if MongoDB has all images
            for image in _apiImages:
                if image not in _catImages:
                    print('new image: ' + image)
                    _catImages.append(image)

            # Update image array of cat if it has new photos
            filter = {"_id": breed["id"]}
            changes = {"$set": {"images": _catImages}}
            collection.update_one(filter, changes)

# Insert all new cats
if len(listCatsToInsert) > 0:
    collection.insert_many(listCatsToInsert)