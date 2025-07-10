#!/usr/bin/env python3
"""
Audio Routing Fix Script

This script helps diagnose and fix audio routing issues with BlackHole.
It provides step-by-step instructions and verification tests.
"""

import subprocess
import time
import sys
from pathlib import Path

def check_blackhole_installation():
    """Check if BlackHole is properly installed."""
    print("🔍 Checking BlackHole Installation...")
    
    try:
        # Check if BlackHole devices exist
        result = subprocess.run(['system_profiler', 'SPAudioDataType'], 
                              capture_output=True, text=True)
        
        if 'BlackHole' in result.stdout:
            print("✅ BlackHole is installed")
            if 'BlackHole 2ch' in result.stdout:
                print("✅ BlackHole 2ch found")
            if 'BlackHole 16ch' in result.stdout:
                print("✅ BlackHole 16ch found")
            return True
        else:
            print("❌ BlackHole not found")
            print("📥 Install BlackHole from: https://github.com/ExistentialAudio/BlackHole")
            return False
            
    except Exception as e:
        print(f"❌ Error checking BlackHole: {e}")
        return False

def get_current_audio_devices():
    """Get current default audio devices."""
    print("\n🎤 Current Audio Device Settings...")
    
    # Method 1: Try osascript
    try:
        # Get input device
        result = subprocess.run([
            'osascript', '-e', 
            'tell application "System Preferences" to return (get current input device of sound preferences)'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"🎤 Current Input: {result.stdout.strip()}")
        
        # Get output device  
        result = subprocess.run([
            'osascript', '-e',
            'tell application "System Preferences" to return (get current output device of sound preferences)'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"🔊 Current Output: {result.stdout.strip()}")
            
    except Exception as e:
        print(f"⚠️ Could not get device info via osascript: {e}")

def create_multi_output_device():
    """Instructions for creating Multi-Output Device."""
    print("\n🔧 CREATING MULTI-OUTPUT DEVICE")
    print("=" * 50)
    print("1. Open 'Audio MIDI Setup' application")
    print("   (Spotlight: Audio MIDI Setup)")
    print("")
    print("2. Click the '+' button → 'Create Multi-Output Device'")
    print("")
    print("3. In the Multi-Output Device:")
    print("   ✅ Check 'Built-in Output' (your speakers/headphones)")
    print("   ✅ Check 'BlackHole 2ch'")
    print("   ✅ Set 'BlackHole 2ch' as MASTER device (checkbox)")
    print("")
    print("4. Rename it to 'Multi-Output Device'")
    print("")
    input("Press Enter when you've completed these steps...")

def set_system_audio_devices():
    """Instructions for setting system audio devices."""
    print("\n⚙️ SETTING SYSTEM AUDIO DEVICES")
    print("=" * 50)
    print("1. Open System Preferences → Sound")
    print("")
    print("2. Go to OUTPUT tab:")
    print("   🔊 Select 'Multi-Output Device'")
    print("   (This sends audio to both speakers AND BlackHole)")
    print("")
    print("3. Go to INPUT tab:")
    print("   🎤 Select 'BlackHole 2ch'")
    print("   (This allows apps to capture from BlackHole)")
    print("")
    input("Press Enter when you've completed these steps...")

def test_audio_routing():
    """Test the audio routing setup."""
    print("\n🧪 TESTING AUDIO ROUTING")
    print("=" * 50)
    
    # Test 1: Play system audio
    print("Test 1: System Audio → BlackHole")
    print("1. Open YouTube or Music app")
    print("2. Play some audio")
    print("3. You should hear it through your speakers/headphones")
    print("   (because Multi-Output Device includes Built-in Output)")
    print("")
    
    # Test 2: Record from BlackHole
    print("Test 2: BlackHole → Recording")
    print("1. Keep the audio playing")
    print("2. We'll test if BlackHole receives it...")
    print("")
    
    input("Press Enter to run the BlackHole recording test...")
    
    # Store original directory
    import os
    original_cwd = os.getcwd()
    
    # Quick recording test
    try:
        import sys
        
        # Add project paths
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        sys.path.insert(0, str(project_root / "src"))
        
        # Change to project directory for proper imports
        os.chdir(str(project_root))
        
        from src.audio.capture import AudioCapture
        from src.utils.config import Config
        import numpy as np
        
        print("🎙️ Recording 3 seconds from BlackHole...")
        capture = AudioCapture(device=Config.AUDIO_DEVICE_INPUT, sample_rate=Config.SAMPLE_RATE)
        
        if capture.start_recording():
            chunks = []
            start_time = time.time()
            
            while time.time() - start_time < 3.0:
                chunk = capture.get_audio_chunk(timeout=0.1)
                if chunk is not None:
                    chunks.append(chunk)
                time.sleep(0.01)
            
            capture.stop_recording()
            
            if chunks:
                audio_data = np.concatenate(chunks)
                max_amplitude = np.max(np.abs(audio_data))
                rms_amplitude = np.sqrt(np.mean(audio_data.astype(float) ** 2))
                
                print(f"📊 Recording Results:")
                print(f"   Max amplitude: {max_amplitude:.6f}")
                print(f"   RMS amplitude: {rms_amplitude:.6f}")
                
                if max_amplitude > 0.001:
                    print("✅ SUCCESS! BlackHole is receiving audio!")
                    print("   Your audio routing is working correctly.")
                    return True
                else:
                    print("❌ FAILURE! BlackHole is not receiving audio.")
                    print("   Check your Multi-Output Device configuration.")
                    return False
            else:
                print("❌ No audio captured")
                return False
        else:
            print("❌ Failed to start recording from BlackHole")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        # Restore original working directory
        try:
            os.chdir(original_cwd)
        except:
            pass

def google_meet_specific_instructions():
    """Specific instructions for Google Meet."""
    print("\n🎯 GOOGLE MEET SPECIFIC SETUP")
    print("=" * 50)
    print("Google Meet has its own audio device selection!")
    print("")
    print("1. Join a Google Meet meeting")
    print("2. Click the microphone/settings icon")
    print("3. Check microphone settings:")
    print("   🎤 Ensure 'BlackHole 2ch' is NOT selected as microphone")
    print("   🎤 Select your actual microphone (Built-in/external)")
    print("")
    print("4. Check speaker settings:")
    print("   🔊 Select 'Multi-Output Device' or 'Built-in Output'")
    print("")
    print("💡 The AI agent will:")
    print("   - Listen to meeting audio via BlackHole (system-level)")
    print("   - Speak into meeting via its own microphone control")
    print("")

def main():
    """Main diagnostic and fix function."""
    print("🔧 BLACKHOLE AUDIO ROUTING FIX")
    print("=" * 60)
    print("This script will help you fix audio routing issues")
    print("so the AI agent can properly hear Google Meet audio.")
    print("=" * 60)
    
    # Step 1: Check BlackHole installation
    if not check_blackhole_installation():
        print("\n❌ Please install BlackHole first, then re-run this script.")
        return
    
    # Step 2: Check current devices
    get_current_audio_devices()
    
    # Step 3: Create Multi-Output Device
    print("\n" + "="*60)
    response = input("Do you need to create/configure Multi-Output Device? (y/n): ")
    if response.lower().startswith('y'):
        create_multi_output_device()
    
    # Step 4: Set system devices
    print("\n" + "="*60)
    response = input("Do you need to set system audio devices? (y/n): ")
    if response.lower().startswith('y'):
        set_system_audio_devices()
    
    # Step 5: Test audio routing
    print("\n" + "="*60)
    if test_audio_routing():
        print("\n✅ AUDIO ROUTING IS WORKING!")
        print("🚀 Your AI agent should now hear Google Meet audio properly.")
        
        # Step 6: Google Meet specific instructions
        google_meet_specific_instructions()
        
    else:
        print("\n❌ AUDIO ROUTING NEEDS MORE WORK")
        print("💡 Common issues:")
        print("   - Multi-Output Device not configured correctly")
        print("   - BlackHole not set as master in Multi-Output Device")
        print("   - System output not set to Multi-Output Device")
        print("   - No audio currently playing for the test")
        print("")
        print("🔄 Please check the configuration and run the test again.")

if __name__ == "__main__":
    main() 