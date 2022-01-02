import re
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
import nltk
nltk.download('stopwords')
nltk.download('punkt')
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

class Document:
    def __init__(self, content="", date="", typeDoc=""):
        self.content = content;
        self.date = date;
        self.typeDoc = typeDoc;
        
    
        
class TwitterDoc(Document):
    def __init__(self, content="", date="", author="", tweetId=""):
        super().__init__(content, date, "twitter");
        self.author=author;
        self.tweetId=tweetId;
        
    def __str__(self):
        return(self.content)
        
class ArxivDoc(Document):
    def __init__(self, content="", date="", authors="", title=""):
        super().__init__(content, date, "arxiv");
        self.authors=authors;
        self.title=title
        
    def __str__(self):
        return(self.title)
        
class Corpus:
    def __init__(self, nom=""):
        self.nom = nom;
        self.nbDocs = 0;
        self.docs={}
        
    def add(self, doc):
        self.nbDocs += 1
        self.docs[self.nbDocs] = doc
        
    def display(self):
        for doc in self.docs:     
            print(doc,". ",self.docs[doc])
            
             
    #Nettoie chaque texte en mettant tout en minuscule et en enlevant la ponctuation
    def nettoyerTextes(self):
        for doc in self.docs:
            cleanText = self.docs[doc].content   
            cleanText= cleanText.lower()
            cleanText=cleanText.replace("\n"," ")
            
            #Enlève les mots de liaisons qui n'ont pas d'intérêt sémantique
            stop_words = set(stopwords.words('english'))
 
            word_tokens = word_tokenize(cleanText)
 
            cleanList = [w for w in word_tokens if not w.lower() in stop_words]
 
            cleanList = []
 
            for w in word_tokens:
                if w not in stop_words:
                    cleanList.append(w)
                    
            cleanText = ' '.join(cleanList)
            cleanText=re.sub(r'[\.,_?!:;)($%@#/&”“`=+]',' ',cleanText)
            cleanText=re.sub(r'https',' ',cleanText)

            self.docs[doc].content = cleanText
    
    #renvoie les n mots les plus fréquents avec leur fréquence et les documents dans lesquels
    #ils apparaissent
    # n : nbr de mots les plus fréquents à chercher
    def motsFrequents(self,n):
        self.nettoyerTextes()
        voc = pd.DataFrame(None, columns=["mot","freq","docs"])
        for key in self.docs:
            doc = self.docs[key]
            
            mots_doc=doc.content.split()
            if (doc.typeDoc == "arxiv"):
                for mot in mots_doc:
                    #On récupère la ligne correspondant à ce mot, si elle existe
                    index=voc.index[voc["mot"]==mot]
                    #On vérifie s'il existe déjà une ligne correspondant au mot, grace à son index
                    
                    if (index.asi8== None or index.asi8.shape==(0,)):
                        #docsList=[self.docs[key].title]
                        docsList={doc.title : 1}
                        newLine = pd.DataFrame([[mot,1,docsList]], columns=["mot","freq","docs"])
                        voc = pd.concat([voc,newLine], ignore_index=True)
    
                    else: 
                        freq=int(voc.loc[index]["freq"].values) + 1                 
                        docsList = voc.loc[index]["docs"].values[0]
                        
                        if doc.title not in docsList : 
                            docsList[doc.title] = 1
                        else : 
                            docsList[doc.title] += 1
                            
                        voc.loc[index,"docs"]=[docsList]
                        voc.loc[index,"freq"] = freq
                
            else :
                for mot in mots_doc:
                    #On récupère la ligne correspondant à ce mot, si elle existe
                    index=voc.index[voc["mot"]==mot]
                    #On vérifie s'il existe déjà une ligne correspondant au mot, grace à son index
                    
                    if (index.asi8== None or index.asi8.shape==(0,)):
                        
                        docsList={doc.tweetId : 1}
                        newLine = pd.DataFrame([[mot,1,docsList]], columns=["mot","freq","docs"])
                        voc = pd.concat([voc,newLine], ignore_index=True)
    
                    else: 
                        freq=int(voc.loc[index]["freq"].values) + 1                 
                        docsList = voc.loc[index]["docs"].values[0]
                        
                        if doc.tweetId not in docsList : 
                            docsList[doc.tweetId] = 1
                        else : 
                            docsList[doc.tweetId] += 1
                            
                        voc.loc[index,"docs"]=[docsList]
                        voc.loc[index,"freq"] = freq
                    

             
        #On trie tous les mots par fréquence
        #sortedVoc = dict(sorted(vocabulaire.items(), key=lambda item: item[1], reverse=True))
        
        
        

        #On enlève les mots non utiles qui n'ont pas pu être supprimés dans le nettoyage
        #Ces "mots" sont ceux observés en testant l'algorithme avec twitter
        voc = voc.drop(voc[voc.mot=="’"].index)
        voc = voc.drop(voc[voc.mot.str.contains("'")].index)
        voc = voc.drop(voc[voc.mot=="-"].index)
        #Correspond aux urls présents dans les tweets
        voc = voc.drop(voc[voc.mot=="t"].index)
        voc = voc.drop(voc[voc.mot=="co"].index)
        
        voc = voc.sort_values("freq", ascending=False)
        

        return(voc[0:n])
            
        
        