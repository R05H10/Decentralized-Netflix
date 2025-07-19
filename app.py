import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, send_file
from web3 import Web3
import json
import qrcode
import io

# Load environment variables from .env file
load_dotenv()

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Blockchain Connection Setup ---
w3 = Web3(Web3.HTTPProvider(os.getenv("BNB_TESTNET_RPC_URL")))
contract_address = Web3.to_checksum_address(os.getenv("CONTRACT_ADDRESS"))
owner_private_key = os.getenv("OWNER_PRIVATE_KEY")
owner_address = w3.eth.account.from_key(owner_private_key).address

# Load Smart Contract ABI (Application Binary Interface)
with open('contract_abi.json') as f:
    contract_abi = json.load(f)

# Create contract instance
metro_contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# --- Kochi Metro Stations (for a realistic dropdown) ---
kochi_stations = [
    "Aluva", "Palarivattom", "Kaloor", "Town Hall", 
    "Maharaja's College", "MG Road", "Elamkulam", "Vyttila"
]

# --- API Routes ---
@app.route('/')
def index():
    """Renders the main user interface."""
    return render_template('index.html', stations=kochi_stations)

@app.route('/buy_ticket', methods=['POST'])
def buy_ticket():
    """API endpoint to mint a new ticket."""
    try:
        data = request.get_json()
        origin = data['origin']
        destination = data['destination']
        
        # For this demo, we'll mint the ticket to the owner's address.
        user_address = owner_address

        # Build the transaction to call the `mintTicket` function
        nonce = w3.eth.get_transaction_count(owner_address)
        txn = metro_contract.functions.mintTicket(
            user_address, origin, destination
        ).build_transaction({
            'chainId': 97,  # BNB Testnet Chain ID
            'gas': 2000000,
            'gasPrice': w3.to_wei('10', 'gwei'),
            'nonce': nonce,
        })

        # Sign and send the transaction
        signed_txn = w3.eth.account.sign_transaction(txn, private_key=owner_private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # Wait for the transaction to be mined
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        # Get the tokenId from the transaction logs (events)
        transfer_event_log = metro_contract.events.Transfer().process_receipt(tx_receipt)
        token_id = transfer_event_log[0]['args']['tokenId']

        return jsonify({
            "success": True, 
            "message": "Ticket minted successfully!",
            "tokenId": token_id,
            "txHash": tx_hash.hex()
        }), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/get_ticket_qr/<int:token_id>')
def get_ticket_qr(token_id):
    """Generates and returns a QR code for a given ticket ID."""
    try:
        qr_data = str(token_id)
        img = qrcode.make(qr_data)
        
        # Save QR to a memory buffer
        buf = io.BytesIO()
        img.save(buf)
        buf.seek(0)
        
        return send_file(buf, mimetype='image/png')
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)

