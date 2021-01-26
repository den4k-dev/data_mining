from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table

Base = declarative_base()

tags = Table('tags', Base.metadata,
             Column('tag_id', Integer, ForeignKey('tag.id')),
             Column('post_id', Integer, ForeignKey('post.id'))
             )


class Post(Base):
    __tablename__ = 'post'
    id = Column(Integer, autoincrement=True, primary_key=True)
    url = Column(String, nullable=False, unique=True)
    title = Column(String, unique=False, nullable=False)
    first_image_url = Column(String, nullable=False, unique=False)
    created_at = Column(DateTime)
    author_id = Column(Integer, ForeignKey('author.id'))
    author = relationship('Author')
    tags = relationship('Tag', secondary='tags')


class Author(Base):
    __tablename__ = 'author'
    id = Column(Integer, autoincrement=True, primary_key=True)
    url = Column(String, nullable=False, unique=True)
    name = Column(String, unique=False, nullable=False)
    posts = relationship('Post')


class Tag(Base):
    __tablename__ = 'tag'
    id = Column(Integer, autoincrement=True, primary_key=True)
    url = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False, unique=True)
    posts = relationship('Post', secondary='tags')


class Comment(Base):
    __tablename__ = 'comment'
    id = Column(Integer, autoincrement=True, primary_key=True)
    author = Column(String, nullable=False, unique=False)
    text = Column(String, unique=False, nullable=False)
    post_id = Column(Integer, ForeignKey('post.id'))
    post = relationship('Post')
