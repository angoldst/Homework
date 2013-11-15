from flask import Flask, redirect, request, url_for, send_from_directory
from flask.ext.sqlalchemy import SQLAlchemy
#from sqlalchemy import create_engine, MetaData, Table
#from sqlalchemy import *
from werkzeug import secure_filename
from pybtex.database.input import bibtex
import os
import numpy as np

app = Flask(__name__)
dbPresent = []

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data/bibliography.db'
db = SQLAlchemy(app)
app.debug = True

UPLOAD_FOLDER = './data/UPLOAD_FOLDER'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = set(['bib'])

class Article(db.Model):
    '''
    article table which will hold all information for the bibliography. Allows for repeated versions of the article
    based on which collection they are in. Includes reference tag, author list (in string form), journal name, volume
    number, page nubers (in string form), year, title and collection (defined from the url input)
    '''
    id = db.Column(db.Integer, primary_key=True)
    ref_tag = db.Column(db.String(80))
    author_list = db.Column(db.String(150))
    journal = db.Column(db.String(120))
    volume = db.Column(db.Integer)
    pages = db.Column(db.String(20))
    year = db.Column(db.Integer)
    title = db.Column(db.String(120))
    collection = db.Column(db.String(40))


    def __init__(self, ref_tag, author_list, journal, volume, pages, year, title, collection):
        self.ref_tag = ref_tag
        self.author_list = author_list
        self.journal = journal
        self.volume = volume
        self.pages = pages
        self.year = year
        self.title = title
        self.collection = collection

    def __repr__(self):
        return '''<p><br><b>Reference Tag: </b>%s
                          <br><b>Author List: </b>%s'
                          <br><b>Journal: </b>%s
                          <br><b>Volume: </b>%s
                          <br><b>Pages: </b>%s
                          <br><b>Year: </b>%s
                          <br><b>Title: </b>%s
                          <br><b>Collection: </b>%s
                          ''' %(row.ref_tag, row.author_list, row.journal, row.volume, row.pages, row.year, row.title, row.collection)




def allowed_file(filename):
    '''
    ensure that he file name is a .bib file
    '''
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS





#paper = Article('test1', 'test2')
#db.session.add(paper)
#db.session.commit()
#paper = Article('ref', 'list', 'journal', 20, 'pages', 1900, 'title', 'collection' )
#paper2 = Article('ref2', 'list2', 'journal2', 21, 'pages2', 1920, 'title2', 'collection2' )


@app.route('/insert_collection.html', methods=['GET', 'POST'])
def insert_collection():
    '''
    creates a form with a file search to upload .bib file and a text entry for collection name. Will upload the .bib file, convert it to a 
    SQL database and save an upload folder. 
    '''
    global db
    if request.method == 'POST':
        #once the submit button is pressed save the uplaoded .bib file in uploads folder and convert to 
        #SQL database
        file = request.files['file']
        col_name = request.form['col_name']
        if file and allowed_file(file.filename):
            filename = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
            file.save(filename) #save .bib file
            
            #parse bib file into relevent column data and load into article table
            parser = bibtex.Parser()
            bib_data = parser.parse_file(filename)
            
            for n in bib_data.entries:
                cur_ref_tag = n
                author_list =[]
                
                try:
                    for author in bib_data.entries[n].persons['author']:
                        author_list.append(unicode(author).replace('{', '').replace('}', '').encode('ascii', 'replace'))
                except:
                    author_list.append('N/A')
                try:
                    cur_journal =  bib_data.entries[n].fields['journal'].encode('ascii', 'replace')
                except:
                    cur_journal = 'N/A'
                
                try:
                    cur_vol = int(bib_data.entries[n].fields['volume'])
                except:
                    cur_vol = None
                
                try:
                    cur_pages = bib_data.entries[n].fields['pages'].encode('ascii', 'replace')
                except:
                    cur_pages = 'N/A'
                
                try:
                    cur_year = int(bib_data.entries[n].fields['year'])
                except:
                    cur_year = 'N/A'
                
                cur_title = bib_data.entries[n].fields['title'].replace('{', '').replace('}', '').encode('ascii', 'replace')
                
                newPaper = Article(cur_ref_tag, ', '.join(author_list), cur_journal, cur_vol, cur_pages, cur_year, cur_title, col_name)
                db.session.add(newPaper)
                
                db.session.commit()
                #paper = Article('ref', 'list', 'journal', 20, 'pages', 1900, 'title', 'collection' )

            #once database has been created redirect to main page
            return redirect(url_for('start_function'))

    return '''
    <!doctype html>
    <title>BibTex Viewer | Insert a Collection</title>
    <p><a href='%s'>Back to Main Page</a></p>'''  %url_for("start_function") + '''
    <p>A database is present. Please insert a new collection by uploading a BibTex file with the below form.</p>

    <form action="" method="POST" enctype=multipart/form-data>
         <p>Collection Name: <input type="text" name="col_name"/>
         <input type="file" name="file">
         <input type="submit" value=Upload></p>

    </form>
    '''

# @app.route('/data/UPLOAD_FOLDER/<filename>')
# def uploaded_file(filename):
#     '''

#     '''
#     return send_from_directory(app.config['UPLOAD_FOLDER'],
#                                filename)

@app.route('/query.html', methods=['GET', 'POST'])
def run_query():
    '''
    Form that takes a string and runs SQL select statment on bibliography data
    prints results to query page
    '''
    if request.method == 'POST':
        query_text = request.form['query_text']
        eng = db.create_engine('sqlite:///data/bibliography.db')
        #bib_table = db.Table('article', db.metadata, autoload=True, autoload_with=eng)
        try: 
            results =  eng.execute('select * from article WHERE ' + query_text)

        except:
            return '''<!doctype html>
        <title>BibTex Viewer | Run A Query</title>
        <p><a href='%s'>Back to Main Page</a></p>'''  %url_for("start_function") + ''' 
        <form action="query.html" method="POST">
         <p>A database is present. You can query it with the form below. </p>
         <p>Use SQL query syntax to enter the query string that follows the "WHERE".</p>
         <p>Column names are "ref_tag", "author_list", "journal", "volume" (integer), "pages", 
         "year" (integer), "title", and "collection".</p>
         <p>To use wildcards, use "LIKE" and employ the "%" (percent symbol) as multiple character
         wildcard and "_" (underscore) as single character wildcard. </p>
         <p>Make sure to explicitly put strings in quotes.</p>
         <p>Query string:
         <input type="text" name="query_text">
         <input type="submit" value="Query!"></p>

    </form>
    ''' + '<p><b> Error -- invalid search parameters.</b></p>'
        outText = ''
        for row in results:
            outText += '''<p><br><b>Reference Tag: </b>%s
                          <br><b>Author List: </b>%s'
                          <br><b>Journal: </b>%s
                          <br><b>Volume: </b>%s
                          <br><b>Pages: </b>%s
                          <br><b>Year: </b>%s
                          <br><b>Title: </b>%s
                          <br><b>Collection: </b>%s
                          ''' %(row.ref_tag, row.author_list, row.journal, row.volume, row.pages, row.year, row.title, row.collection)
        return '''<!doctype html>
        <title>BibTex Viewer | Run A Query</title>
        <p><a href='%s'>Back to Main Page</a></p>'''  %url_for("start_function") + ''' 
        <form action="query.html" method="POST">
         <p>A database is present. You can query it with the form below. </p>
         <p>Use SQL query syntax to enter the query string that follows the "WHERE".</p>
         <p>Column names are "ref_tag", "author_list", "journal", "volume" (integer), "pages", 
         "year" (integer), "title", and "collection".</p>
         <p>To use wildcards, use "LIKE" and employ the "%" (percent symbol) as multiple character
         wildcard and "_" (underscore) as single character wildcard. </p>
         <p>Make sure to explicitly put strings in quotes.</p>
         <p>Query string:
         <input type="text" name="query_text">
         <input type="submit" value="Query!"></p>

    </form>
    ''' + outText 
    return '''
    <!doctype html>
    <title>BibTex Viewer | Run A Query</title>
    <p><a href='%s'>Back to Main Page</a></p>'''  %url_for("start_function") + ''' 
    <form action="query.html" method="POST">
         <p>A database is present. You can query it with the form below. </p>
         <p>Use SQL query syntax to enter the query string that follows the "WHERE".</p>
         <p>Column names are "ref_tag", "author_list", "journal", "volume" (integer), "pages", 
         "year" (integer), "title", and "collection".</p>
         <p>To use wildcards, use "LIKE" and employ the "%" (percent symbol) as multiple character
         wildcard and "_" (underscore) as single character wildcard. </p>
         <p>Make sure to explicitly put strings in quotes.</p>
         <p>Query string:
         <input type="text" name="query_text">
         <input type="submit" value="Query!"></p>

    </form>
    '''

@app.route("/")
def start_function():
    '''
    At root web directory. When user goes to this site, it begins by checking to see if a database 
    currently exitss. If it does not it will create a new directory saved to data/bibliography.db. 
    It also provides links to either add a new collection or querying an existing database. 
    '''
    #check to see if database exists
    if os.path.isfile('data/bibliography.db'):
        db.create_all()
        
        #Lists current collections available
        cur_collections = ['<p><b>%s</b></p>' %x for x in np.unique(np.array(Article.query.with_entities(Article.collection).filter(Article.collection != None).all(), dtype=str))]
        
        #cur_collections = cur_collections + '</p>'.join(np.unique(np.array(Article.query.with_entities(Article.collection).filter(Article.collection != None).all(), dtype=str)))
        #cur_collections =  ' '.join(np.unique(np.array(Article.query.with_entities(Article.collection).filter(Article.collection != None).all(), dtype=str)))

        return """ <title>BibTex Viewer | Main Page</title>
                    <p><a href='%s'>Insert Collection</a> -- <a href='%s'>Run Query</a></p>
                    <p> A database is present. These are your available collections: </p>
                    <p> %s </p>""" % (url_for("insert_collection"), url_for("run_query"), ''.join(cur_collections))
    else:
        db.create_all()
        return """ <title>BibTex Viewer | Main Page</title>
                    <p><a href='%s'>Insert Collection</a> -- <a href='%s'>Run Query</a></p>
                    <p> No database present, one has been created for you. </p>""" % (url_for("insert_collection"), url_for("run_query"))


    #print " ".join([str(x) for x in Article.query.all()])
    #return repr([x for x in Article.query.all()])

#@app.route("/admin")
#def get_admin_email():
#   admin = User.query.filter_by(username='admin').first()
#   return "<b>Admin Email</b>: %s" % admin.email

if __name__ == "__main__":
    app.run()

