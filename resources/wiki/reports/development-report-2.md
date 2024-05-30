**Project Development Progress Report**
## <a name="_4sj3dl13s56b"></a>**1. Creation of a Google Cloud Account**
The initial step of our project involved setting up a Google Cloud account, for which a credit card was utilized. This step was essential to access the wide array of services offered by Google Cloud for our project needs.
## <a name="_y9c09ogtpi6b"></a>**2. PostgreSQL Instance Setup**
A new PostgreSQL database instance was successfully created on Google Cloud. This database was configured to store the data for our project.
## <a name="_5kodnakgivh2"></a>**3. Establishing a Localhost Tunnel from PyCharm to Google Cloud**
Using the PyCharm IDE, a localhost tunnel was opened to securely connect to our PostgreSQL database on Google Cloud. The tunnel was set to listen on localhost:5432. This allowed us to access our database seamlessly from our local development environment.
## <a name="_7btmc1lhd389"></a>**4. Reviewing PRAW Documentation**
To interact with Reddit, the Python Reddit API Wrapper (PRAW) was employed. The documentation for PRAW was thoroughly reviewed to gain the necessary knowledge for efficiently fetching data from Reddit.
## <a name="_vb1q1byg2u2n"></a>**5. Data Fetching in reddit.py from main.py**
As part of the project, the reddit.py file was configured to fetch data from the main.py file. This setup was designed as part of the modular structure of our project.
## <a name="_2jfd7cx98mn"></a>**6. Retrieval of HotPosts from Reddit**
Hotposts from Reddit were fetched using the RedditPost object. This object ensured that the fetched data was stored in an organized and manageable format.
##
## <a name="_np2j27atxby0"></a><a name="_vdpy4bkpkaob"></a>**7. Opening a Database Connection**
A database connection was successfully established for the project. This connection was necessary for transferring the fetched data into our database.
## <a name="_73cag26tke7y"></a>**8. Writing Insert Statements**
Insert statements necessary for adding data to our database were written. These commands ensured the proper storage of fetched data into our database.
## <a name="_e7iydktg8lh8"></a>**9. Insertion of Posts from Subreddits into the Database**
Posts fetched from various subreddits began to be inserted into our database using the previously written insert statements. During this process, duplicate posts were handled using a special logic, ensuring that only unique posts were added to our database.
## <a name="_lpvdt32960ji"></a>**Conclusion**
This report summarizes the processes from creating a PostgreSQL database instance on Google Cloud to fetching data from Reddit and storing it in our database. With these steps successfully completed, our project now has the infrastructure required for effective data collection and management. This integration will form a solid foundation for data analysis and visualization efforts in later stages of the project.

