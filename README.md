## Welcome to VIP Text Editor Factorial Program (VIP for short).      

<p align="left">
  <img src="https://github.com/user-attachments/assets/9d0cf566-ea7e-4eb5-9283-9a47e7762eb0" width="150" height="150" alt="VIP Editor Icon" />
</p>

I would like to welcome you to the world of VIP.      
VIP is a text editor written in Python that allows you to do quick terminal edits with ease. A preview is attached below.      

<img width="700" height="320" alt="Screenshot 2026-05-15 at 5 45 04 PM" src="https://github.com/user-attachments/assets/1e4dd3da-89d8-4a6f-90e5-ae9bc14a5c20" />    

As you can see this is a CLI only text editor and let us put an imaginary use case. Say you loaded up VIP and now need to create and load a file named jello.py. Preview below:      

<img width="2304" height="1034" alt="image" src="https://github.com/user-attachments/assets/f37f865a-0ad8-4c92-8743-3aceb7aba4f1" />. 

In addition, this is a list of ALL keyboard shortcuts:
* `^W` Write Mode 
* `^E` Insert mode 
* `^Q` Exit No Save 
* `^Y` Save Insert 
* `^X` Exit Write 
* `^T` Exit Insert 
* `^G` Exit Save All

## Tech Stack
Now that I have explained how to *use* the VIP Text Editor Factorial Program, I will explain its tech stack. 
The tech stack is a basic python script, which uses the built-in libraries `curses` and `os`.  
It is written for maximum compatibility with Unix®-like or Unix®-based operating systems.     

## Licensing and CLI Commandwork and General Installation
This is under the BSD 3 License.     
In order to install and run, use any of these two tactics: 

### 1. SUDO APT
Do this with the following command:

 ```bash
 echo "deb [trusted=yes] https://live-by-unix.github.io/VIP-DEBIAN/ ./" | sudo tee /etc/apt/sources.list.d/vip-editor.list
sudo apt update && sudo apt install vip-editor
```

### 2. Python way (latest updates)         
Download the newest release and unzip it.        
Then
```bash 
cd path/to/your/vip/build 
```
and run python3 vip.py and do some testing.              
In order to alias it, this is the drill.      
```bash 
nano ~/.bashrc # Or zshrc for mac.
 ```      
Then add this at the bottom,       
 ```bash 
 alias vip-editor='python3 /path/to/your/vip/vip.py' ```     
 # Then save your changes and do
source ~/.bashrc # Or zshrc on mac
```   
And pow! You have the VIP Text Editor Factorial Program 
### How VIP works. 
VIP keyboard shortcuts are pretty self explanatory (see above), so mainly this is about the difference between WRITE and INSERT mode.         
In Vim, you know write as browsing the file like a view-only google doc, and insert to actually insert text. But it's different in VIP.        
Write Mode: Writes directly to the text file, as usual, just like text editors like BBEdit, Nano, or even VSCode.           
Insert Mode: creates a text version of your current file (if you were editing jello.py, insert mode would create a file named jello.py.txt).     
It will copy over everything from the original document you were editing (say jello.py) and all the changes your write in insert mode will be saved to the text file.     
In order to delete jello.py and rename jello.py.txt to jello.py (keeping your changes in normal talk) do ^Y. To delete jello.py.txt and switch back to editing jello.py, do ^T.    
To save your insert changes ONLY and exit, do ^T, which exits and saves only your write mode changes.     
To save only your write mode changes do ^Y.     
To exit and save both write and insert mode, do ^G.        

And BOOM! Now you can use the VIP Text Editor! 


