import json
import threading
import time
import re
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Import pyscard for PC/SC communication
try:
    from smartcard.System import readers
    from smartcard.CardType import AnyCardType
    from smartcard.CardRequest import CardRequest
    from smartcard.util import toHexString, toBytes
    from smartcard.Exceptions import CardRequestTimeoutException, NoCardException
    PYSCARD_AVAILABLE = True
except ImportError:
    PYSCARD_AVAILABLE = False

# Global variables to track NFC reader state
nfc_reader = None
card_monitor_thread = None
is_monitoring = False
last_card_data = None
last_card_id = None

def initialize_reader():
    """
    Initialize the PC/SC NFC reader
    """
    global nfc_reader
    
    if not PYSCARD_AVAILABLE:
        return False, "PyScard library not available. Install using: pip install pyscard"
    
    try:
        # Get available readers
        available_readers = readers()
        
        if not available_readers:
            return False, "No PC/SC readers found. Make sure your ACR 122u is connected."
        
        # Look for a reader that matches ACR 122u
        for reader in available_readers:
            reader_name = str(reader).lower()
            if "acr122" in reader_name or "acr 122" in reader_name:
                nfc_reader = reader
                return True, str(reader)
        
        # If no ACR 122u found, use the first available reader
        nfc_reader = available_readers[0]
        return True, str(nfc_reader)
        
    except Exception as e:
        return False, str(e)

def read_card_data(timeout=1):
    """
    Read data from an NFC card
    """
    global nfc_reader
    
    if not nfc_reader:
        success, message = initialize_reader()
        if not success:
            return None, None
    
    try:
        # Define card type
        card_type = AnyCardType()
        
        # Request card
        card_request = CardRequest(timeout=timeout, cardType=card_type, readers=[nfc_reader])
        card_service = card_request.waitforcard()
        
        # Connect to card
        card_service.connection.connect()
        
        # Get card UID/serial number
        get_uid_command = [0xFF, 0xCA, 0x00, 0x00, 0x00]
        data, sw1, sw2 = card_service.connection.transmit(get_uid_command)
        
        if sw1 == 0x90 and sw2 == 0x00:  # Success
            card_id = toHexString(data).replace(' ', '')
            print(f"Card UID: {card_id}")
            
            # For specific ACR122u cards that give strange output, try new approach
            card_data = read_specific_card_format(card_service)
            if card_data:
                print(f"Specific card format data: {card_data}")
                # Remove "ten" prefix if present
                card_data = remove_Ten_prefix(card_data)
                return card_data, card_id
            
            # Method 1: Try to read as NDEF
            card_data = read_ndef_data(card_service)
            if card_data:
                print(f"NDEF data read: {card_data}")
                # Remove "ten" prefix if present
                card_data = remove_Ten_prefix(card_data)
                # Clean up the data if it looks like a corrupted string
                cleaned_data = clean_card_data(card_data)
                if cleaned_data != card_data:
                    print(f"Cleaned data: {cleaned_data}")
                    return cleaned_data, card_id
                return card_data, card_id
                
            # Method 2: Try to read as MIFARE Classic
            card_data = read_mifare_data(card_service)
            if card_data:
                print(f"MIFARE data read: {card_data}")
                # Remove "ten" prefix if present
                card_data = remove_Ten_prefix(card_data)
                # Clean up the data if it looks like a corrupted string
                cleaned_data = clean_card_data(card_data)
                if cleaned_data != card_data:
                    print(f"Cleaned data: {cleaned_data}")
                    return cleaned_data, card_id
                return card_data, card_id
                
            # Method 3: Try direct read of card memory
            card_data = read_card_memory(card_service)
            if card_data:
                print(f"Card memory data: {card_data}")
                # Remove "ten" prefix if present
                card_data = remove_Ten_prefix(card_data)
                # Clean up the data if it looks like a corrupted string
                cleaned_data = clean_card_data(card_data)
                if cleaned_data != card_data:
                    print(f"Cleaned data: {cleaned_data}")
                    return cleaned_data, card_id
                return card_data, card_id
            
            # If all methods fail, return just the UID
            print("All reading methods failed, returning UID")
            return card_id, card_id
        else:
            print(f"Failed to get card UID. Status: {sw1:02X} {sw2:02X}")
            return None, None
            
    except CardRequestTimeoutException:
        # Timeout, no card detected
        return None, None
    except NoCardException:
        # No card present
        return None, None
    except Exception as e:
        print(f"Error reading card: {str(e)}")
        return None, None

def remove_Ten_prefix(data):
    """
    Remove "Ten" prefix from card data if present 
    """
    if isinstance(data, str):
        # Check if data starts with "Ten" followed by actual content (exact case match)
        if data.startswith("Ten"):
            print(f"Removing 'Ten' prefix from: {data}")
            return data[3:]
            
        # Also handle other case variations (ten, TEN, etc.)
        if data.lower().startswith("ten"):
            print(f"Removing 'ten' prefix (case insensitive) from: {data}")
            return data[3:]
            
        # Also handle case where it might have spaces
        if data.lower().startswith("ten "):
            print(f"Removing 'ten ' prefix from: {data}")
            return data[4:]
            
        # Also try other variations like "ten-" or "ten:"
        if re.match(r'^ten[-: ]', data, re.IGNORECASE):
            print(f"Removing 'ten' prefix with separator from: {data}")
            match = re.match(r'^ten[-: ]+(.*)', data, re.IGNORECASE)
            if match:
                return match.group(1)
    
    return data

def clean_card_data(data):
    """
    Clean up card data that might be corrupted or incorrectly decoded
    """
    # First remove any "ten" prefix
    data = remove_Ten_prefix(data)
    
    # If data matches the pattern of corrupted strings like ':}r5H}r5H5HTeTengya',
    # try to extract any meaningful part
    if isinstance(data, str):
        # Look for alphanumeric sequences that might be student IDs
        # Student IDs are usually alphanumeric and at least 4-5 characters
        student_id_pattern = re.compile(r'[A-Za-z0-9]{4,}')
        matches = student_id_pattern.findall(data)
        
        if matches:
            # Return the longest match as it's most likely to be the actual ID
            longest_match = max(matches, key=len)
            print(f"Extracted potential student ID: {longest_match}")
            return longest_match
            
        # If data contains mostly non-printable characters or strange symbols,
        # it might be binary data incorrectly interpreted as text
        if sum(c.isalnum() for c in data) < len(data) * 0.5:
            # In this case, just extract the alphanumeric characters
            alphanumeric = ''.join(c for c in data if c.isalnum())
            if len(alphanumeric) >= 4:  # Only return if we have enough characters
                print(f"Extracted alphanumeric data: {alphanumeric}")
                return alphanumeric
    
    # If it's a hex string and looks like it might be a UID,
    # clean it up to just be the hex digits
    if isinstance(data, str) and all(c in '0123456789ABCDEFabcdef ' for c in data):
        cleaned = data.replace(' ', '')
        if 8 <= len(cleaned) <= 32:  # Typical UID length range when represented as hex
            print(f"Cleaned hex string: {cleaned}")
            return cleaned
    
    # No cleaning needed or possible
    return data

def read_specific_card_format(card_service):
    """
    Try to read the specific format used by the cards producing strings like ':}r5H}r5H5HTeTengya'
    """
    try:
        print("Attempting to read specific card format...")
        
        # Try reading all sectors and blocks to find meaningful data
        all_data_blocks = []
        
        # Read all data blocks (excluding sector trailers)
        for sector in range(16):  # MIFARE Classic 1K has 16 sectors
            for block in range(4):  # Each sector has 4 blocks
                block_number = sector * 4 + block
                
                # Skip sector trailer (block 3, 7, 11, etc.)
                if block == 3:
                    continue
                    
                read_command = [0xFF, 0xB0, 0x00, block_number, 0x10]  # Read 16 bytes
                response, sw1, sw2 = card_service.connection.transmit(read_command)
                
                if sw1 == 0x90 and sw2 == 0x00:
                    # Check if this block contains meaningful data (not just zeros)
                    if any(b != 0 for b in response):
                        # Add block number and data for analysis
                        all_data_blocks.append((block_number, response))
        
        # Process all collected blocks to look for patterns
        if all_data_blocks:
            print(f"Read {len(all_data_blocks)} non-empty blocks")
            
            # Try different encoding schemes
            for block_num, block_data in all_data_blocks:
                # Try UTF-8 encoding
                try:
                    utf8_text = bytes(block_data).decode('utf-8', errors='ignore')
                    # Check if it contains mostly printable characters
                    printable_ratio = sum(c.isprintable() and not c.isspace() for c in utf8_text) / len(utf8_text)
                    if printable_ratio > 0.7:  # If more than 70% is printable
                        print(f"Block {block_num} has readable UTF-8: {utf8_text}")
                        # Remove "ten" prefix if present
                        cleaned_text = remove_Ten_prefix(utf8_text.strip())
                        return cleaned_text
                except:
                    pass
                
                # Try ASCII encoding for blocks with printable characters
                ascii_chars = []
                for b in block_data:
                    if 32 <= b <= 126:  # Printable ASCII
                        ascii_chars.append(chr(b))
                
                if ascii_chars and len(ascii_chars) > 4:  # If we have a reasonable amount of ASCII
                    ascii_text = ''.join(ascii_chars)
                    print(f"Block {block_num} has ASCII data: {ascii_text}")
                    
                    # If it looks like a student ID or similar pattern
                    if re.match(r'^[A-Za-z0-9]+$', ascii_text):
                        # Remove "ten" prefix if present
                        cleaned_text = remove_Ten_prefix(ascii_text)
                        return cleaned_text
            
            # If no single block had clear text, try to combine blocks from sector 1
            # (often used for user data)
            sector1_data = []
            for block_num, block_data in all_data_blocks:
                if 4 <= block_num <= 6:  # Blocks in sector 1 (excluding trailer)
                    sector1_data.extend(block_data)
            
            if sector1_data:
                # Try to extract ASCII from combined sector data
                ascii_chars = []
                for b in sector1_data:
                    if 32 <= b <= 126:  # Printable ASCII
                        ascii_chars.append(chr(b))
                
                if ascii_chars and len(ascii_chars) > 4:
                    combined_text = ''.join(ascii_chars)
                    print(f"Combined sector 1 ASCII: {combined_text}")
                    
                    # Try to extract student ID pattern
                    matches = re.findall(r'[A-Za-z0-9]{4,}', combined_text)
                    if matches:
                        longest_match = max(matches, key=len)
                        print(f"Extracted ID from sector 1: {longest_match}")
                        # Remove "ten" prefix if present
                        cleaned_match = remove_Ten_prefix(longest_match)
                        return cleaned_match
        
        return None
        
    except Exception as e:
        print(f"Error in specific card format reading: {str(e)}")
        return None

def read_ndef_data(card_service):
    """
    Read NDEF data from an NFC card
    """
    try:
        print("Attempting to read NDEF data...")
        
        # Select NDEF application (standard NDEF file)
        select_ndef_command = [0x00, 0xA4, 0x04, 0x00, 0x07, 0xD2, 0x76, 0x00, 0x00, 0x85, 0x01, 0x01, 0x00]
        response, sw1, sw2 = card_service.connection.transmit(select_ndef_command)
        
        print(f"NDEF application select response: {sw1:02X} {sw2:02X}")
        
        if sw1 != 0x90 or sw2 != 0x00:
            print("Failed to select NDEF application")
            
            # Try alternative NDEF selection (some cards use this format)
            alt_select_command = [0x00, 0xA4, 0x04, 0x00, 0x07, 0xD2, 0x76, 0x00, 0x00, 0x85, 0x01, 0x00]
            response, sw1, sw2 = card_service.connection.transmit(alt_select_command)
            
            print(f"Alternative NDEF select response: {sw1:02X} {sw2:02X}")
            
            if sw1 != 0x90 or sw2 != 0x00:
                print("Failed to select alternative NDEF application")
                return None
        
        # Read NDEF file control info to get the exact location
        get_ndef_file_info = [0x00, 0xA4, 0x00, 0x0C, 0x02, 0xE1, 0x04]
        response, sw1, sw2 = card_service.connection.transmit(get_ndef_file_info)
        
        print(f"NDEF file info response: {sw1:02X} {sw2:02X}")
        
        # Some cards don't support this command, so we'll try direct reading if it fails
        if sw1 != 0x90 or sw2 != 0x00:
            print("Failed to get NDEF file info, trying direct read")
        
        # Read NDEF data length (standard approach)
        read_len_command = [0x00, 0xB0, 0x00, 0x00, 0x02]
        response, sw1, sw2 = card_service.connection.transmit(read_len_command)
        
        print(f"NDEF length read response: {sw1:02X} {sw2:02X}, data: {toHexString(response) if response else 'None'}")
        
        # If standard approach fails, try alternative approach (some cards store length differently)
        if sw1 != 0x90 or sw2 != 0x00 or len(response) < 2:
            print("Standard length read failed, trying alternative approach")
            
            # Try reading more data to find length marker
            alt_read_command = [0x00, 0xB0, 0x00, 0x00, 0x0F]  # Read first 15 bytes
            response, sw1, sw2 = card_service.connection.transmit(alt_read_command)
            
            print(f"Alternative read response: {sw1:02X} {sw2:02X}, data: {toHexString(response) if response else 'None'}")
            
            if sw1 != 0x90 or sw2 != 0x00 or len(response) < 3:
                print("Alternative read also failed")
                return None
                
            # Try to locate NDEF message TLV (Type-Length-Value) structure
            # Type 0x03 is NDEF message
            ndef_start = None
            for i in range(len(response) - 2):
                if response[i] == 0x03:  # NDEF Message TLV
                    ndef_start = i
                    break
                    
            if ndef_start is not None:
                ndef_length = response[ndef_start + 1]  # Length in TLV
                print(f"Found NDEF TLV at position {ndef_start}, length: {ndef_length}")
                
                # Read full data based on found length
                if ndef_length > 0:
                    read_data_command = [0x00, 0xB0, 0x00, ndef_start + 2, ndef_length]
                    response, sw1, sw2 = card_service.connection.transmit(read_data_command)
                    
                    if sw1 == 0x90 and sw2 == 0x00 and len(response) > 0:
                        result = parse_ndef_message(response)
                        return remove_Ten_prefix(result)
            
            # If we couldn't find a TLV structure, try reading blocks directly
            return None
            
        # Standard approach successful - get the length
        ndef_length = (response[0] << 8) + response[1]
        print(f"NDEF length: {ndef_length}")
        
        if ndef_length > 0 and ndef_length < 1000:  # Sanity check on length
            # Read the actual NDEF data
            read_data_command = [0x00, 0xB0, 0x00, 0x02, ndef_length]
            response, sw1, sw2 = card_service.connection.transmit(read_data_command)
            
            print(f"NDEF data read response: {sw1:02X} {sw2:02X}, data length: {len(response) if response else 0}")
            
            if sw1 == 0x90 and sw2 == 0x00 and len(response) > 0:
                result = parse_ndef_message(response)
                return remove_Ten_prefix(result)
        else:
            print(f"Invalid NDEF length: {ndef_length}")
        
        return None
        
    except Exception as e:
        print(f"Error reading NDEF data: {str(e)}")
        return None

def parse_ndef_message(data):
    """
    Parse NDEF message data to extract text content
    """
    try:
        print(f"Parsing NDEF data: {toHexString(data)}")
        
        # Check if this is valid NDEF data
        if len(data) < 3:
            print("Data too short for NDEF")
            return None
            
        # Try to find text records
        # NDEF Text record has type "T" (0x54)
        # Format: [Header byte][Type length][Payload length][Type][Status byte][Language code][Text]
        i = 0
        while i < len(data):
            # Try to decode as text assuming it's a valid NDEF message
            try:
                # Look for record header
                if i + 3 >= len(data):
                    break
                    
                header = data[i]
                type_length = data[i + 1]
                payload_length = data[i + 2]
                
                print(f"Record at position {i}: header={header:02X}, type_length={type_length}, payload_length={payload_length}")
                
                if type_length == 0 or payload_length == 0 or i + 3 + type_length + payload_length > len(data):
                    i += 1
                    continue
                    
                record_type = data[i + 3:i + 3 + type_length]
                payload = data[i + 3 + type_length:i + 3 + type_length + payload_length]
                
                # Check if this is a Text record (type "T")
                if type_length == 1 and record_type[0] == 0x54:  # "T" for Text
                    print("Found Text record")
                    
                    # Text record format: [Status byte][Language code][Text]
                    # Status byte: bit 7 is UTF-8/UTF-16, bits 0-5 are language code length
                    status_byte = payload[0]
                    lang_length = status_byte & 0x3F  # Lower 6 bits
                    
                    # Skip language code to get to the text
                    text_start = 1 + lang_length
                    if text_start < len(payload):
                        text_bytes = payload[text_start:]
                        text = "".join(chr(b) for b in text_bytes)
                        print(f"Extracted text: {text}")
                        # Remove any "ten" prefix
                        text = remove_Ten_prefix(text)
                        return text
                
                # Move to next record
                i += 3 + type_length + payload_length
                
            except Exception as inner_e:
                print(f"Error parsing NDEF record at position {i}: {str(inner_e)}")
                i += 1
        
        # If we couldn't find a Text record, try to extract any readable text
        # This is a fallback for non-standard or corrupted NDEF data
        readable_chars = []
        for byte in data:
            if 32 <= byte <= 126:  # Printable ASCII
                readable_chars.append(chr(byte))
        
        if readable_chars:
            text = "".join(readable_chars)
            print(f"Extracted text from raw data: {text}")
            # Remove any "ten" prefix
            text = remove_Ten_prefix(text)
            return text
            
        # If all else fails, return the hex string
        return toHexString(data)
        
    except Exception as e:
        print(f"Error parsing NDEF message: {str(e)}")
        return toHexString(data)  # Return hex string as fallback

def read_mifare_data(card_service):
    """
    Read data from a MIFARE Classic card
    """
    try:
        print("Attempting to read MIFARE data...")
        
        # MIFARE cards require authentication
        # Try to authenticate with default keys for sector 1
        # Default key A: FF FF FF FF FF FF
        auth_command_a = [0xFF, 0x86, 0x00, 0x00, 0x05, 0x01, 0x00, 0x01, 0x60, 0x00]
        response, sw1, sw2 = card_service.connection.transmit(auth_command_a)
        
        print(f"Auth response with key A: {sw1:02X} {sw2:02X}")
        
        if sw1 != 0x90 or sw2 != 0x00:
            # Try alternative key B: FF FF FF FF FF FF
            auth_command_b = [0xFF, 0x86, 0x00, 0x00, 0x05, 0x01, 0x00, 0x01, 0x61, 0x00]
            response, sw1, sw2 = card_service.connection.transmit(auth_command_b)
            
            print(f"Auth response with key B: {sw1:02X} {sw2:02X}")
            
            if sw1 != 0x90 or sw2 != 0x00:
                print("Authentication failed with default keys")
                return None
        
        # Read data from blocks 4-7 (sector 1)
        all_data = []
        
        for block in range(4, 8):
            read_command = [0xFF, 0xB0, 0x00, block, 0x10]  # Read 16 bytes
            response, sw1, sw2 = card_service.connection.transmit(read_command)
            
            print(f"Block {block} read response: {sw1:02X} {sw2:02X}")
            
            if sw1 == 0x90 and sw2 == 0x00:
                all_data.extend(response)
        
        if all_data:
            # Try to convert to text
            readable_chars = []
            for byte in all_data:
                if 32 <= byte <= 126:  # Printable ASCII
                    readable_chars.append(chr(byte))
            
            if readable_chars:
                text = "".join(readable_chars)
                print(f"Extracted text from MIFARE data: {text}")
                # Remove any "ten" prefix
                text = remove_Ten_prefix(text)
                return text
                
            return toHexString(all_data)
            
        return None
        
    except Exception as e:
        print(f"Error reading MIFARE data: {str(e)}")
        return None

def read_card_memory(card_service):
    """
    Try direct memory reading as a last resort
    """
    try:
        print("Attempting direct memory read...")
        
        # Try reading several blocks directly
        all_data = []
        
        # Read first 4 blocks (16 bytes each)
        for block in range(4):
            read_command = [0xFF, 0xB0, 0x00, block, 0x10]  # Read 16 bytes
            response, sw1, sw2 = card_service.connection.transmit(read_command)
            
            print(f"Memory block {block} read response: {sw1:02X} {sw2:02X}")
            
            if sw1 == 0x90 and sw2 == 0x00:
                all_data.extend(response)
        
        if all_data:
            # Try to convert to text
            readable_chars = []
            for byte in all_data:
                if 32 <= byte <= 126:  # Printable ASCII
                    readable_chars.append(chr(byte))
            
            if readable_chars:
                text = "".join(readable_chars)
                print(f"Extracted text from direct memory: {text}")
                # Remove any "ten" prefix
                text = remove_Ten_prefix(text)
                return text
                
            return toHexString(all_data)
            
        return None
        
    except Exception as e:
        print(f"Error reading card memory: {str(e)}")
        return None

def card_monitor_loop():
    """
    Background thread to monitor for NFC cards
    """
    global is_monitoring, last_card_data, last_card_id
    
    while is_monitoring:
        try:
            card_data, card_id = read_card_data(timeout=1)
            
            if card_data and card_id:
                # Remove "ten" prefix if present (final check)
                if isinstance(card_data, str):
                    card_data = remove_Ten_prefix(card_data)
                
                # Store the card data
                last_card_data = card_data
                last_card_id = card_id
                
                # Sleep to avoid multiple reads of the same card
                time.sleep(3)
            
            # Small sleep to reduce CPU usage
            time.sleep(0.2)
            
        except Exception as e:
            print(f"Error in card monitor loop: {str(e)}")
            time.sleep(1)  # Sleep longer on error

@csrf_exempt
def nfc_status(request):
    """
    API endpoint to check NFC reader status
    """
    if request.method == 'GET':
        if not PYSCARD_AVAILABLE:
            return JsonResponse({
                'status': 'error',
                'message': 'PyScard library not available. Install using: pip install pyscard'
            })
        
        success, message = initialize_reader()
        
        if success:
            return JsonResponse({
                'status': 'success',
                'message': 'NFC reader connected',
                'reader_name': message
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': message
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })

@csrf_exempt
def nfc_read(request):
    """
    API endpoint to read an NFC card
    """
    global is_monitoring, last_card_data, last_card_id, card_monitor_thread
    
    if request.method == 'GET':
        if not PYSCARD_AVAILABLE:
            return JsonResponse({
                'status': 'error',
                'message': 'PyScard library not available'
            })
        
        # Start the monitor thread if it's not already running
        if not is_monitoring:
            is_monitoring = True
            card_monitor_thread = threading.Thread(target=card_monitor_loop)
            card_monitor_thread.daemon = True
            card_monitor_thread.start()
        
        # Check if we have new card data
        if last_card_data:
            # Final check to remove "ten" prefix if present
            if isinstance(last_card_data, str):
                last_card_data = remove_Ten_prefix(last_card_data)
                
            response_data = {
                'status': 'success',
                'card_data': last_card_data,
                'card_id': last_card_id
            }
            
            # Clear the stored data after returning it
            last_card_data = None
            last_card_id = None
            
            return JsonResponse(response_data)
        
        return JsonResponse({
            'status': 'waiting',
            'message': 'No card detected'
        })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })

@csrf_exempt
def nfc_stop(request):
    """
    API endpoint to stop the NFC reader
    """
    global is_monitoring, card_monitor_thread
    
    if request.method == 'POST':
        is_monitoring = False
        
        # Wait for the thread to finish if it exists
        if card_monitor_thread and card_monitor_thread.is_alive():
            card_monitor_thread.join(timeout=2)
        
        card_monitor_thread = None
        
        return JsonResponse({
            'status': 'success',
            'message': 'NFC reader stopped'
        })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }) 