###################################### LIBRARIES ##########################################
# import required libraries
import time
import requests
from datetime import datetime, timezone
from openai import AzureOpenAI
import os
# import openai
import json
from typing import Optional, Union, Any, Dict

######################################### VARIABLES DECLARATION ###########################
# global variables declarations
# variables related to Azure AI-Search
AZURE_SERVICE_NAME = "starlink-aisearch-nprd"
AZURE_SEARCH_API_VERSION = "2020-06-30"
AZURE_SEARCH_INDEX = "shipment-data-index"
AZURE_SEARCH_ENDPOINT = "https://starlink-aisearch-nprd.search.windows.net"
AZURE_SEARCH_ENDPOINT_C = f"https://{AZURE_SERVICE_NAME}.search.windows.net/indexes/{AZURE_SEARCH_INDEX}/docs/search?api-version={AZURE_SEARCH_API_VERSION}"

# variables related to Azure OpenAI
AZURE_OPENAI_API_KEY = "rEgv1GQVyOg1JjyskTQd2twIRroog6lVfrIkRMTUHstO8lxTCTaOJQQJ99BFACHYHv6XJ3w3AAABACOG41dX"
AZURE_OPENAI_ENDPOINT = "https://starlink-openai-nprd.openai.azure.com/openai/deployments/gpt-35-turbo-starlink/chat/completions?api-version=2025-01-01-preview"
AZURE_OPENAI_DEPLOYMENT = "gpt-35-turbo-starlink"
AZURE_OPENAI_DEPLOYMENT_NAME = "gpt-35-turbo-starlink"
AZURE_OPENAI_API_VERSION = "2023-12-01-preview"

# primary cred to use
SECRET_1 = "EtbxI75wdOgVThA39ziNcN21rsbIOO2738rzV5VImjAzSeAOLkHy"


########################################## SETTING UP LOG ################################
# setup a log file for chatbot response history and performance for further investigation

def get_current_working_directory() -> str:
    return os.getcwd()

log_file = "chatbot_logs.jsonl"


def log_interaction(user_query: str, bot_response: str, latency: float, is_correct: Optional[bool]=None) ->None:
    log_entry: dict[str, Union[str, float, bool, None]] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": user_query,
        "response": bot_response,
        "latency_sec": latency,
        "correct": is_correct
    }
    try:
        with open(log_file, "a") as file:
            file.write(json.dumps(log_entry) + "\n")
    except IOError as e:
        # basic error handling for file operations
        print(f"Error writing to log file: {e}")        


########################## CUSTOM FUNCTION FOR SEARCH AND FETCH DATA ###########################
# setup a query enviornment for fetching information for ai-search
def query_azure_search(user_query: str)-> Dict[str, Any]:
    headers: Dict[str, str] = {
        "Content-Type": "application/json",
        "api-key": SECRET_1
    }
    payload:Dict[str, Union[str, int]] = {
        "search": user_query,
        "queryType": "simple",
        "top": 5
    }
    response = requests.post(AZURE_SEARCH_ENDPOINT_C, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


############################# CUSTOM FUNCTION FOR USER INTERACTION WITH CHATBOT###################
# setup a chat enviornment for user interaction
# define field mappings
FIELD_MAPPINGS: Dict[str, str] = {
    "Container Number": "ContainerNo",
    "Container Type": "ContainerTy",
    "Destination Service": "DestinationSer",
    "Load Port": "LoadPort",
    "Final Load Port": "FinalLoadPort",
    "Discharge Port": "DischargePort",
    "Last CY Location": "LastCyLoc",
    "Place of Receipt": "ReceiptLoc",
    "Place of Delivery": "DeliveryPlace",
    "Final Destination": "FinalDestination",
    "First Vessel Code": "FirstVesselCd",
    "First Vessel Name": "FirstVesselNm",    
    "First Voyage code": "FirstVoyageCd",    
    "Final Carrier Code": "FinalCarrierCd",    
    "Final Carrier SCAC Code": "FinalCarrierCdSCAC",    
    "Final Carrier Name": "FinalCarrierNm",    
    "Final Vessel Code": "VesselCdFinal",    
    "Final Vessel Name": "VesselNmFinal",    
    "Final Voyage code": "VoyageCdFinal",    
    "True Carrier Code": "CarrierCdTrue",    
    "True Carrier SCAC Code": "CarrierCdTrueSCAC",    
    "True Carrier SCAC Code_1": "CarrierCdTrueSCAC1",    
    "Supplier/Vendor Name": "SupVenNm",    
    "Manufacturer Name": "ManufacNm",    
    "Ship To Party Name": "Ship2PartyNm",    
    "Booking Approval Status": "BookingApprovalStatus",    
    "Service Contract Number": "ServiceContractNo",    
    "Carrier Vehicle Load Lcn": "CarrierVehLoadLoc",    
    "Vehicle Departure Lcn": "VehDepartureLoc",    
    "Vehicle Arrival Lcn": "VehArrivalLoc",    
    "Carrier Vehicle Unload Lcn": "CarrierVehUnloadLoc",    
    "Out Gate Location": "OutGateLoc",    
    "Equipment Arrival at Last Lcn": "EquipArrivalLastLoc",    
    "Out gate at Last CY Lcn": "OutGateLastLocCY",    
    "Delivery Date To Consignee Lcn": "DelDate2ConsigneeLoc",    
    "Booking Number (Multiple)": "BookingNoMt",    
    "Empty Container Return Lcn": "EmptyContainerReturnLoc",    
    "FCR Number (Multiple)": "FCRNoMt",    
    "Ocean BL No (Multiple)": "OceanBLNoMt",    
    "PO Number (Multiple)": "PurOrdNoMt",    
    "Consignee Code (Multiple)": "ConsigneeCdMt",    
    "Cargo Received Date (Multiple)": "CargoReceivedDtMt",    
    "Hot Container Flag": "IsHot",    
    "Late Booking Status": "IsBookedLate",    
    "Current Departure status": "IsCurrDepartued",    
    "Current Arrival status": "IsCurrArrived",    
    "Late Arrival status": "IsArrivedLate",    
    "Late Container Return status": "IsContainerReturnLate",    
    "ETD LP": "LoadPortETD",    
    "ETD FLP": "FinalLoadPortETD",    
    "ETA DP": "DischargePortETA",    
    "ETA FD": "FinalDestinationETA",    
    "Revised ETA": "RevisedETA",    
    "Predictive ETA": "PredictiveETA",    
    "ATD LP": "LoadPortATD",    
    "ATA FLP": "FinalLoadPortATA",    
    "ATD FLP": "FinalLoadPortATD",    
    "ATA DP": "DischargePortATA",    
    "Revised ETA FD": "RevisedFinalDestinationETA",    
    "Predictive ETA FD": "PredictiveFinalDestinationETA",    
    "CARRIER VEHICLE LOAD Date": "CarrierVehLoadDt",    
    "Vehicle Departure Date": "VehDepartureDt",    
    "Vehicle Arrival Date": "VehArrivalDt",    
    "Carrier Vehicle Unload Date": "CarrierVehUnloadDt",    
    "Out Gate Date From DP": "DischargePortOutGateDt",    
    "Equipment Arrived at Last CY": "LastCyEquipArrivedDt",    
    "Out gate at Last CY": "LastCyOutGateDt",    
    "Delivery Date To Consignee": "ConsigneeDeliveryDt",    
    "Empty Container Return Date": "EmptyContainerReturnDt",    
    "Detention Free Days": "DetFreeDy",    
    "Demurrage Free Days": "DemFreeDy",    
    "CO2 Emission For Tank On Wheel": "CO2EmsTW",    
    "CO2 Emission For Well To Wheel": "CO2EmsWW",    
    "calc_duration": "DurDy",    
    "calc_delay": "DelDy",
}

# define system prompt using field mappings
def get_system_prompt() ->str:
    fields: str = ', '.join(FIELD_MAPPINGS.values())
    return (
        "You are an AI-powered logistics assistant specializing in shipment data. "
        "Answer questions ONLY using the provided data from Azure AI Search. "
        "If you don’t know, say 'I don’t have that information but still learning.'\n\n"
        "Key rules MUST follow:\n"
        f"Use only the following fields from shipment-data-index: {fields}.\n"
        "Never invent details.\n"
        "Format dates as DD-MMM-YYYY (e.g., 13-Jan-2025)."
    )


# reusable function to get assistant response
def query_chatbot(user_query: str) -> Union[str, Any]:
    start_time = time.time()
    print(f"Start time: {start_time}")

    
    try:
        system_prompt = get_system_prompt()
        search_results = query_azure_search(user_query)
        documents = [doc.get("content", "") for doc in search_results.get("value", [])]
        context = "\n\n".join(documents)

        openai_client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            _strict_response_validation=False
        )


        response = openai_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {user_query}"}
            ]
        )

        bot_response: Union[str, Any] = response.choices[0].message.content
        end_time = time.time()
        latency = end_time - start_time
        print(f"Bot Responded Time: {end_time}")
        print(f"Time taken by bot: {latency:0.2f} sec")
        log_interaction(user_query, bot_response, latency)
        return bot_response

    except Exception as err:
        print(f"System encountered an error: {err}")
        return None
    
    
# example use case
if __name__ == "__main__":
    while (user_query := input("\nUser: ")).lower() not in ["e", "q", "exit", "quit"]:
        print("\nBot: ", end=" ")
        bot_response = query_chatbot(user_query)
        print(bot_response)