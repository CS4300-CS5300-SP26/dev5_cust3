# Information about working with our production server
## DO Droplet Info
- IP: 24.144.92.128
- Root Password: Elk7-Basket
- Django User Password: Django

## Server Commands
When working on the server, run as django not root unless absolutely necessary. 
### Git Commands
Make sure to run a git pull inside the repository before doing any work to ensure that the server is up to date. You should generally not do any development on the actual server, instead pull changes on the server to git. Minor configuration changes are acceptable.
  
git branch -b <my_feature> // Creates a new feature branch  
git status // Check which files have been changed from the HEAD  
git add <files> // Stage files for commit  
git commit // Commit all staged files on the branch  
git push // Pushes comitted changes to the GitHub repository from the server  


### Start the server cold
sudo systemctl start nginx  
sudo systemctl status nginx  
sudo systemctl start gunicorn  
sudo systemctl status gunicorn  

### Reloading the server after making/pulling changes
sudo systemctl reload nginx  
sudo systemctl status nginx  
sudo systemctl reload gunicorn  
sudo systemctl status gunicorn  
