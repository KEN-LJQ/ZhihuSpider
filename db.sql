create database proxy_ip;

use proxy_ip;

create table ip_list
(
	id int auto_increment primary key,
    proxy_ip varchar(20) not null,
    proxy_port varchar(10) not null,
    proxy_address varchar(20),
    proxy_protocal varchar(10) not null,
    proxy_alive_time varchar(20),
    proxy_validate_time varchar(20)
);

use proxy_ip;

create table user_info
(
	id int auto_increment primary key,
    user_avator_url varchar(50),
    user_token varchar(50) not null,
    user_name varchar(30) not null,
    user_headline varchar(100),
    user_location varchar(100),
    user_business varchar(50),
    user_employments varchar(100),
    user_educations varchar(100),
    user_description varchar(150),
    user_sinaweibo_url varchar(50),
    user_gender int,
    user_following_count int,
    user_follower_count int,
    user_answer_count int,
    user_question_count int,
    user_voteup_count int
);

create table user_list_cache
(
	user_token varchar(50) primary key
);
