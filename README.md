## Welcome to TUI VIP Text Editor Factorial Program (VIP for short).      

<p align="left">
  <img src="https://github.com/user-attachments/assets/9d0cf566-ea7e-4eb5-9283-9a47e7762eb0" width="150" height="150" alt="VIP Editor Icon" />
</p> 
VIP is a special TUI (Terminal User Interface) Text Editor.     
This README.md is divided into five sections. Intro, How to Install, How to Use, and Conclusion.     
Previews of the VIP text editor are show below.    
<img width="2356" height="1033" alt="Screenshot 2026-05-17 at 9 25 14 AM" src="https://github.com/user-attachments/assets/bbf1cb43-631a-475c-bd75-8419f3384722" />
<img width="2355" height="1027" alt="Screenshot 2026-05-17 at 9 24 52 AM" src="https://github.com/user-attachments/assets/71e403ff-4710-429b-adfb-a442e22208b5" />     

## Installation.    
And disclaimer: People who went digging through the version history (you're a chad) and found a SUDO APT method, I hate to break the news, BUT that port is deleted.     
Why? Well it's because the debian path was wayyyyy to hard to maintain and pushing updates took a long time and a lot of work for a limited Linux audience (Debian based only).    
And great news, I HAVE A HOMEBREW PORT OPEN! It was supposed to be open at the end of May 2026, but I got a tap ready! 
* Number 1 # git clone with the command below or download the latest release zip and unzip.  
To git clone, do this command 
``` bash
git clone https://github.com/live-by-unix/VIP.git
```
Once you have the full repo and have cded in the folder with vip.py, run 
````bash
python3 vip.py
````
If it works and you have VIP, of course you're gonna alias it. Here is the code block to do so.     
``` bash
nano ~/.bashrc # Or zshrc on zsh shells & macOS.
```
Then put this following code block in your bashrc or zshrc: 
``` bash
alias vip-editor='python3 /path/to/your/vip/vip.py'
``` 
Once done, run 
```` bash
source ~/.bashrc # or zshrc on zsh shells & macOS.
````
* Number 2: Homebrew
Homebrew installation can be done with this one simple code block
```bash
brew tap live-by-unix/vip
brew trust live-by-unix/vip
brew update
brew install vip-editor
```
Now you can use VIP with vip-editor! 

### How to use. 
Once you tested vip-editor works, how do you create your first file?     
Well, the keyboard shortcuts explain for themselves, but I will explain write and insert quickly, for now read this bullet point list.    
* **^W** Writes directly to a file
* **^E** Enters Insert mode.
* **^Q** Exit without saving ANY changes.
* **^Y** Commit your Insert changes.
* **^X** Save ONLY Write changes and exit.
* **^B** Save ONLY Insert changes and exit.
* **^T** Exits and deletes the Insert file and goes back to Write.
* **^G** Save ALL changes (Write and Insert) and exit.
* **^F** Finds text in your current file.
* **^Z** Undos the last change. 
  
Now, I will explain Insert and Write.    
Write is normally writing your changes directly to the file.    
Insert is creating a .txt version of your file (if editing jello.java, insert would create a file named jello.java.txt)     
You can insert a insert, and write a insert, kinda like a Russian Nestling Doll.  
To save a insert to the original file toy inserted, do ^Y. To delete a insert and go back to the last insert of write, do ^T.   
All the other shortcuts are find or Exit and do something, but whatever.     

### And this is the end.     
I hope you will enjoy and use the **TUI VIP Text Editor Factorial Program.**    
And this is it, this is under BSD-3.0 License, and free to use.    
Homebrew coming soon! 

### **IMPORTANT NOTICE, WILL NOT BE IN THE RELEASE README.MD, PLS READ NOW.** 
**When using VIP, if you do not specify the file extension (hello doesn't have the .txt, bye doesn't have the .java, you know) THE FILE may COME UP EMPTY. SO PLEASE ALWAYS INCLUDE FILE EXTENSION.**


