## Welcome to VIP Text Editor Factorial Program (VIP for short).      
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
# 1. Register your GitHub Pages APT repository
echo "deb [trusted=yes] https://github.io stable main" | sudo tee /etc/apt/sources.list.d/vip-editor.list

# 2. Synchronize your package indexes
sudo apt update

# 3. Pull and install VIP Editor!
sudo apt install vip-editor
```
Now you can use it with vip-editor

2. Python way:
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



