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
### How VIP Works

VIP keyboard shortcuts are pretty self-explanatory, so the main concept to understand is the unique architectural difference between **WRITE** and **INSERT** mode. 

In Vim, you look at "Normal" mode as a way to navigate or browse the file like a view-only Google Doc, and "Insert" mode to actually type text. **VIP flips this concept on its head.**

* **WRITE Mode:** This is your primary editor state. It writes directly to your active working memory buffer—exactly like standard non-modal text editors such as Nano, BBEdit, or VSCode. 
* **INSERT Mode (Triggered with `^E`):** This is your experimental staging ground. When you enter INSERT mode, VIP takes an isolated snapshot of your current file state. You can think of it like working on a temporary version (`jello.py.txt`). You can type, delete, and experiment freely in this sandbox without risking your stable baseline code.

#### Merging and Aborting Changes

Because of this dual-buffer system, you have complete version control over your text right from your keyboard shortcuts:

* **`^Y` (Save/Merge Insert):** Copies all your experimental updates from the INSERT buffer back into your primary WRITE buffer, updating your main file state and returning you to WRITE mode. (Like running a `git merge`).
* **`^T` (Exit/Abort Insert):** Drops your experimental INSERT buffer entirely from memory, discarding your recent playground edits and snapping you safely back to your untouched, original WRITE state. (Like running a `git checkout -- file`).
* **`^G` (Exit Save All):** Instantly flushes your active buffer straight to your storage drive and quits the application immediately.

And **BOOM!** Now you can use the VIP Text Editor with total confidence!


