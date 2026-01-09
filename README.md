<h1>Instructions</h1>

<p>To run your Python code on another computer, follow these standard steps:</p>
<h2>1. Download the Project</h2>
<p>On the new computer, open a terminal or command prompt and clone your repository:</p>
<code>
git clone [your-repository-url]
cd [your-project-folder]
</code>

<h2>2. Create a New Virtual Environment</h2>
<p>You must create a fresh .venv on the new machine because virtual environments are not portable between computers. </p>
<code>
python -m venv .venv
</code>

<h2>3. Activate the Environment</h2>
<p>You need to enter the environment so your commands affect this project only. </p>
<code>
.venv\Scripts\activate
source .venv/bin/activate
</code>
<p> To run the scrapper in env<p>
<code>
.venv/bin/python scraper.py
</code>

<h2>4. Install Dependencies</h2>
<p>Now, use the requirements.txt file you created earlier to install all necessary libraries at once.</p> 
<code>
pip install -r requirements.txt
</code>

<h1>Scenario B: Updating existing files (Pulling)</h1>
<p>If you already have the project on your computer but made changes on another device (or directly on GitHub), use the pull command to sync them. <br>
Open Terminal: Navigate into your project folder.<br>
Run the Pull:</p>
<code>
git pull origin main
</code>

What this does: It "fetches" the changes from GitHub and "merges" them into your current local files automatically.<br>
Update Dependencies: If you added new libraries to requirements.txt on the other computer, run the install command again to update your local .venv:
<code>
pip install -r requirements.txt
</code>
