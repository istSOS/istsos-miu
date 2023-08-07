import httpx
import traceback
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi import status
from app.sta2rest import sta2rest

v1 = APIRouter()
    
def get_result_type_and_column(input_string):
    try:
        value = eval(str(input_string))
    except (SyntaxError, NameError):
        result_type = 0
        column_name = "resultString"
    else:
        if isinstance(value, int):
            result_type = 1
            column_name = "resultInteger"
        elif isinstance(value, float):
            result_type = 2
            column_name = "resultDouble"
        elif isinstance(value, dict):
            result_type = 4
            column_name = "resultJSON"
        else:
            result_type = None
            column_name = None

    if input_string == "true" or input_string == "false":
        result_type = 3
        column_name = "resultBoolean"

    if result_type is not None:
        return result_type, column_name
    else:
        raise Exception("Cannot cast result to a valid type")
    
def flatten_entity_body(entity, body, name = None):

    # check if entity is an array
    if isinstance(entity, list):
        # loop trought all the values
        for item in entity:
            # create the entity
            flatten_entity_body(item, body, name)
        return body

    for key in list(entity):
        if isinstance(key, str) and key in sta2rest.STA2REST.ENTITY_MAPPING:
            converted_key = sta2rest.STA2REST.convert_entity(key)
            body[converted_key] = entity[key]
            
            flatten_entity_body(entity[key], body, converted_key)
            
            if name:
                if isinstance(body[name], list):
                    for item in body[name]:
                        item[converted_key] = {
                            "@iot.id": entity[key]["@iot.id"] if "@iot.id" in entity[key] else None
                        }
                else:
                    body[name][converted_key] = {
                        "@iot.id": entity[key]["@iot.id"] if "@iot.id" in entity[key] else None
                    }

    return body

def format_entity_body(entity_body): 
    # Check if entity_body is an array
    if isinstance(entity_body, list):
        # Loop trought all the values
        for i in range(len(entity_body)):
            # Create the entity
            entity_body[i] = format_entity_body(entity_body[i])
        return entity_body

    formatted_body = {}
    # Loop trought all the keys in the body
    for key in entity_body:
        if isinstance(key, str) and key in sta2rest.STA2REST.ENTITY_MAPPING:
            if "@iot.id" in entity_body[key]:
                new_key = sta2rest.STA2REST.convert_to_database_id(key)
                formatted_body[new_key] = entity_body[key]["@iot.id"]
        elif key == "result":
            value = entity_body["result"]
            result_type, column_name = get_result_type_and_column(value)
            formatted_body[column_name] = value
            formatted_body["resultType"] = result_type
        else:
            formatted_body[key] = entity_body[key]

    return formatted_body

async def create_entity(entity_name, body):

    entity_body = {
        entity_name: body
    }

    body = flatten_entity_body(entity_body, entity_body)


    # Creation order
    created_ids = {}
    creation_order = ["Location","Thing", "Sensor", "ObservedProperty", "FeaturesOfInterest", "Datastream", "Observation"]
    for entity_name in creation_order:
        if entity_name in body:
            
            formatted_body = format_entity_body(body[entity_name])

            if "@iot.id" in formatted_body:
                continue

            # check if the entity has sub entities and if they are empty check if id is present
            if isinstance(formatted_body, list):
                for item in formatted_body:
                    for key in item:
                        if key in created_ids:
                            item[key] = created_ids[key]
            else:
                for key in formatted_body:
                    # check if key is present in created_ids
                    if key in created_ids:
                        formatted_body[key] = created_ids[key]

            url = "http://postgrest:3000/" + entity_name

            print("Creating entity: ", entity_name)
            print("Body: ", formatted_body)
            
            async with httpx.AsyncClient() as client:   
                # post to postgrest
                r = await client.post(url, json=formatted_body, headers={"Prefer": "return=representation"})

                # get response
                result = r.json()

                # print r status
                if r.status_code != 201:
                    raise PostgRESTError(result["message"])
                
                # get first element of the result
                result = result[0]

                # get the id of the created entity
                id_key = sta2rest.STA2REST.convert_to_database_id(entity_name)
                created_ids[id_key] = result["id"]

                print("Created entity: ", id_key, " with id: ", result["id"])

    return None


# Handle POST requests
@v1.api_route("/{path_name:path}", methods=["POST"])
async def catch_all_post(request: Request, path_name: str):
    # Accept only content-type application/json
    if not "content-type" in request.headers or request.headers["content-type"] != "application/json":
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "code": 400,
                "type": "error",
                "message": "Only content-type application/json is supported."
            }
        )

    try:
        full_path = request.url.path
        # parse uri
        result = sta2rest.STA2REST.parse_uri(full_path)
        # get json body
        body = await request.json()
        main_table = result["entity"][0]
        result = await create_entity(main_table, body)
        # Return okay
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "code": 200,
                "type": "success",
                "message": result
            }
        )
        
    except Exception as e:
        # print stack trace
        traceback.print_exc()
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "code": 400,
                "type": "error",
                "message": str(e)
            }
        )