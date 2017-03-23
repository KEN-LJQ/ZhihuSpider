CREATE DATABASE spider_test
DEFAULT CHARACTER SET utf8
DEFAULT COLLATE utf8_general_ci;

use spider_test;

CREATE TABLE user_info
(
	id int auto_increment primary key,
    user_avator_url varchar(50),
    user_token varchar(50) unique not null,
    user_name varchar(30) not null,
    user_headline varchar(100),
    user_location varchar(100),
    user_business varchar(50),
    user_employments varchar(100),
    user_educations varchar(100),
    user_description varchar(150),
    user_gender int,
    user_following_count int,
    user_follower_count int,
    user_answer_count int,
    user_question_count int,
    user_voteup_count int,
    index(user_token)
)ENGINE=InnoDB DEFAULT CHARACTER SET=utf8;