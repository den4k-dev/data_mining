from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models


class Database:
    def __init__(self, db_url):
        engine = create_engine(db_url)
        models.Base.metadata.create_all(bind=engine)
        self.session_m = sessionmaker(bind=engine)

    def get_or_create(self, session, model, **data):
        db_model = session.query(model).filter(model.url == data['url']).first()
        if not db_model:
            db_model = model(**data)
        return db_model

    def create_post(self, data):
        session = self.session_m()
        author = self.get_or_create(session, models.Author, **data['author'])
        post = self.get_or_create(session, models.Post, **data['post_data'], author=author)
        for comment in data['comments']:
            data_comment = {
                'author': comment['user']['full_name'],
                'text': comment['body']
            }
            comment = models.Comment(**data_comment, post=post)
            session.add(comment)
        for item in data['tags']:
            tag = self.get_or_create(session, models.Tag, **item)
            post.tags.append(tag)
        session.add(post)
        try:
            session.commit()
        except Exception as err:
            session.rollback()
        finally:
            session.close()



