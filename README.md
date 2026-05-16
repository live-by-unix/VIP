## Welcome to VIP Text Editor Factorial Program (VIP for short).          
<img width="150" height="150" alt="gemini-svg" src="https://github.com/user-attachments/assets/9d0cf566-ea7e-4eb5-9283-9a47e7762eb0" />
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <!-- Background Squircle (Rounded Square) -->
  <rect width="512" height="512" rx="100" fill="#1A1B26"/>
  
  <!-- Terminal Window Control Buttons -->
  <circle cx="80" cy="80" r="15" fill="#F7768E"/>
  <circle cx="130" cy="80" r="15" fill="#E0AF68"/>
  <circle cx="180" cy="80" r="15" fill="#9ECE6A"/>

  <!-- "VIP" Text - Using standard cross-platform Monospace font stack -->
  <text x="50%" y="300" 
        font-family="Monaco, 'Courier New', Courier, monospace" 
        font-size="140" 
        font-weight="900" 
        fill="#C0CAF5" 
        text-anchor="middle">VIP</text>
  
  <!-- Terminal Cursor (the blinking block style) -->
  <rect x="345" y="210" width="60" height="100" fill="#7AA2F7">
    <animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite" />
  </rect>

  <!-- Subtitle for that "Pro" feel -->
  <text x="50%" y="420" 
        font-family="Monaco, 'Courier New', Courier, monospace" 
        font-size="28" 
        fill="#565F89" 
        text-anchor="middle" 
        letter-spacing="5">Terminal Editor</text>
</svg>

I would like to welcome you to the world of VIP.      
VIP is a text editor written in Python that allows you to do quick terminal edits with ease. A preview is attached below.      
<img width="700" height="320" alt="Screenshot 2026-05-15 at 5 45 04 PM" src="https://github.com/user-attachments/assets/1e4dd3da-89d8-4a6f-90e5-ae9bc14a5c20" />    
As you can see this is a CLI only text editor and let us put a imaginary use case. Say you loaded up VIP and now need to create and load a file named jello.py. Preview below:        
<img width="2304" height="1034" alt="image" src="https://github.com/user-attachments/assets/f37f865a-0ad8-4c92-8743-3aceb7aba4f1" />. 
In addition, this is a list of ALL keyboard shortcuts. ^W Write Mode  ^E Insert mode  ^Q Exit No Save  ^Y Save Insert  ^X Exit Write  ^T Exit Insert  ^G Exit Save All.        

## Tech Stack
Now that I have explained how to *use* the VIP Text Editor Factorial Program, I will explain it's tech stack. 
The tech stack is a basic python script, which uses the built in libraries curses and os.  
It is written for maxiumum compatibility with Unix®-like or Unix®-based operating systems.     

## Licensing and CLI commandwork and general installatiom
This is under the BSD 3 License.     
In order to install and run use these two tatics: 
1. SUDO APT: do with this command:
```bash
echo "deb [trusted=yes] [https://live-by-unix.github.io/VIP-DEBIAN/](https://live-by-unix.github.io/VIP-DEBIAN/) ./" | sudo tee /etc/apt/sources.list.d/vip-editor.list
sudo apt update && sudo apt install vip-editor

Now you can use it with vip-editor command to run. 

3. Python way:
Clone this github repo 
```bash
git clone https://github.com/live-by-unix/VIP.git
```
Once cloned, cd and run vip.py to test. In order to alias run this command: 
```bash
# Add the alias to your bash profile (replace /path/to/cloned/repo with the actual folder path)
echo "alias vip='python3 /path/to/cloned/repo/vip.py'" >> ~/.bashrc

# Reload bash to apply the changes immediately
source ~/.bashrc
```
### Well done!
Now you have the VIP Text Editor Factorial Program. 



