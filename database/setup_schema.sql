-- Setup script for research_papers schema and tables
-- Run this script to create the database structure and sample data

-- Create schema
CREATE SCHEMA IF NOT EXISTS research_papers;

-- Create ai_research_papers table
CREATE TABLE IF NOT EXISTS research_papers.ai_research_papers (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    authors TEXT[] NOT NULL,
    abstract TEXT,
    publication_date DATE,
    journal VARCHAR(200),
    doi VARCHAR(100),
    keywords TEXT[],
    citation_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create research_topics table
CREATE TABLE IF NOT EXISTS research_papers.research_topics (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,
    parent_topic_id INTEGER REFERENCES research_papers.research_topics(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create paper_topics junction table
CREATE TABLE IF NOT EXISTS research_papers.paper_topics (
    paper_id INTEGER REFERENCES research_papers.ai_research_papers(id) ON DELETE CASCADE,
    topic_id INTEGER REFERENCES research_papers.research_topics(id) ON DELETE CASCADE,
    PRIMARY KEY (paper_id, topic_id)
);

-- Insert sample research topics
INSERT INTO research_papers.research_topics (name, description) VALUES
('Machine Learning', 'Algorithms and techniques for machine learning'),
('Natural Language Processing', 'Processing and understanding human language'),
('Computer Vision', 'Image and video analysis'),
('Deep Learning', 'Neural networks and deep architectures'),
('Reinforcement Learning', 'Learning through interaction with environment'),
('AI Ethics', 'Ethical considerations in artificial intelligence'),
('Large Language Models', 'Large-scale language models and transformers')
ON CONFLICT (name) DO NOTHING;

-- Insert sample AI research papers
INSERT INTO research_papers.ai_research_papers (title, authors, abstract, publication_date, journal, doi, keywords, citation_count) VALUES
(
    'Attention Is All You Need',
    ARRAY['Ashish Vaswani', 'Noam Shazeer', 'Niki Parmar', 'Jakob Uszkoreit', 'Llion Jones', 'Aidan N. Gomez', 'Łukasz Kaiser', 'Illia Polosukhin'],
    'The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.',
    '2017-06-12',
    'Advances in Neural Information Processing Systems',
    '10.48550/arXiv.1706.03762',
    ARRAY['transformer', 'attention', 'neural networks', 'sequence modeling'],
    45000
),
(
    'BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding',
    ARRAY['Jacob Devlin', 'Ming-Wei Chang', 'Kenton Lee', 'Kristina Toutanova'],
    'We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers.',
    '2018-10-11',
    'NAACL',
    '10.18653/v1/N19-1423',
    ARRAY['bert', 'language model', 'pre-training', 'transformers'],
    35000
),
(
    'Generative Adversarial Networks',
    ARRAY['Ian J. Goodfellow', 'Jean Pouget-Abadie', 'Mehdi Mirza', 'Bing Xu', 'David Warde-Farley', 'Sherjil Ozair', 'Aaron Courville', 'Yoshua Bengio'],
    'We propose a new framework for estimating generative models via an adversarial process, in which we simultaneously train two models: a generative model G that captures the data distribution, and a discriminative model D that estimates the probability that a sample came from the training data rather than G.',
    '2014-06-10',
    'Advances in Neural Information Processing Systems',
    '10.48550/arXiv.1406.2661',
    ARRAY['gan', 'generative models', 'adversarial training', 'deep learning'],
    42000
),
(
    'ResNet: Deep Residual Learning for Image Recognition',
    ARRAY['Kaiming He', 'Xiangyu Zhang', 'Shaoqing Ren', 'Jian Sun'],
    'Deeper neural networks are more difficult to train. We present a residual learning framework to ease the training of networks that are substantially deeper than those used previously. We explicitly reformulate the layers as learning residual functions with reference to the layer inputs, instead of learning unreferenced functions.',
    '2015-12-10',
    'IEEE Conference on Computer Vision and Pattern Recognition',
    '10.1109/CVPR.2016.90',
    ARRAY['resnet', 'residual networks', 'image recognition', 'deep learning'],
    38000
),
(
    'AlphaGo: Mastering the Game of Go with Deep Neural Networks and Tree Search',
    ARRAY['David Silver', 'Aja Huang', 'Chris J. Maddison', 'Arthur Guez', 'Laurent Sifre', 'George van den Driessche', 'Julian Schrittwieser', 'Ioannis Antonoglou', 'Veda Panneershelvam', 'Marc Lanctot', 'Sander Dieleman', 'Dominik Grewe', 'John Nham', 'Nal Kalchbrenner', 'Ilya Sutskever', 'Timothy Lillicrap', 'Madeleine Leach', 'Koray Kavukcuoglu', 'Thore Graepel', 'Demis Hassabis'],
    'The game of Go has long been viewed as the most challenging of classic games for artificial intelligence owing to its enormous search space and the difficulty of evaluating board positions and moves. Here we introduce a new approach to computer Go that uses value networks to evaluate board positions and policy networks to select moves.',
    '2016-01-28',
    'Nature',
    '10.1038/nature16961',
    ARRAY['alphago', 'reinforcement learning', 'game playing', 'deep learning'],
    15000
);

-- Link papers to topics
INSERT INTO research_papers.paper_topics (paper_id, topic_id) VALUES
(1, (SELECT id FROM research_papers.research_topics WHERE name = 'Large Language Models')),
(1, (SELECT id FROM research_papers.research_topics WHERE name = 'Natural Language Processing')),
(2, (SELECT id FROM research_papers.research_topics WHERE name = 'Large Language Models')),
(2, (SELECT id FROM research_papers.research_topics WHERE name = 'Natural Language Processing')),
(3, (SELECT id FROM research_papers.research_topics WHERE name = 'Deep Learning')),
(3, (SELECT id FROM research_papers.research_topics WHERE name = 'Machine Learning')),
(4, (SELECT id FROM research_papers.research_topics WHERE name = 'Computer Vision')),
(4, (SELECT id FROM research_papers.research_topics WHERE name = 'Deep Learning')),
(5, (SELECT id FROM research_papers.research_topics WHERE name = 'Reinforcement Learning')),
(5, (SELECT id FROM research_papers.research_topics WHERE name = 'Deep Learning'));

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_ai_research_papers_title ON research_papers.ai_research_papers(title);
CREATE INDEX IF NOT EXISTS idx_ai_research_papers_authors ON research_papers.ai_research_papers USING GIN(authors);
CREATE INDEX IF NOT EXISTS idx_ai_research_papers_keywords ON research_papers.ai_research_papers USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_ai_research_papers_publication_date ON research_papers.ai_research_papers(publication_date);
CREATE INDEX IF NOT EXISTS idx_paper_topics_paper_id ON research_papers.paper_topics(paper_id);
CREATE INDEX IF NOT EXISTS idx_paper_topics_topic_id ON research_papers.paper_topics(topic_id);

-- Create a view for easy querying of papers with their topics
CREATE OR REPLACE VIEW research_papers.papers_with_topics AS
SELECT 
    p.id,
    p.title,
    p.authors,
    p.abstract,
    p.publication_date,
    p.journal,
    p.doi,
    p.keywords,
    p.citation_count,
    array_agg(t.name) as topics
FROM research_papers.ai_research_papers p
LEFT JOIN research_papers.paper_topics pt ON p.id = pt.paper_id
LEFT JOIN research_papers.research_topics t ON pt.topic_id = t.id
GROUP BY p.id, p.title, p.authors, p.abstract, p.publication_date, p.journal, p.doi, p.keywords, p.citation_count;

-- Grant permissions (adjust as needed for your setup)
GRANT USAGE ON SCHEMA research_papers TO PUBLIC;
GRANT SELECT ON ALL TABLES IN SCHEMA research_papers TO PUBLIC;
GRANT SELECT ON research_papers.papers_with_topics TO PUBLIC;
