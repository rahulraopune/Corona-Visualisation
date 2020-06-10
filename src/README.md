Step 1: Install pip3

Step 2: Install virtual environment using this command 

        pip3 install virtualenv

Step 3: From the root directory in command line and run the following command to activate the virtual environment.

        source src/bin/activate

    Note: You have to activate whenever you close and reopen VSCode or Terminal. 


Step 4: Install the dependent packages using the following command

        pip install -r requirements.txt



You can see the list of packages installed using the following command:
    
        pip3 list

Whenever you install any new package please run the following command so that after pushing to Git, anyone can just install the required packages from the requirements.txt file.

        pip3 freeze > requirements.txt