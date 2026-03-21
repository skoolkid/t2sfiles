/* 
 * Generate library titles (ZXDB 1.0.183+).
 */

create table entry_library_titles (
  entry_id int(11) not null,
  title varchar(250) not null,
  library_title varchar(250) not null
);

insert into entry_library_titles
select id, title, title from entries;

update entry_library_titles as e
set library_title = trim(substr(e.title, length(p.text) + 1) || ', ' || substr(e.title, 1, length(p.text)))
from prefixes as p
where e.title like p.text || '%';

update entry_library_titles as e
set library_title = title
from prefixexempts as p
where e.title like p.text || '%';


create table alias_library_titles (
  entry_id int(11) not null,
  title varchar(250) not null,
  library_title varchar(250) not null
);

insert into alias_library_titles
select entry_id, title, title from aliases;

update alias_library_titles as a
set library_title = trim(substr(a.title, length(p.text) + 1) || ', ' || substr(a.title, 1, length(p.text)))
from prefixes as p
where a.title like p.text || '%';

update alias_library_titles as a
set library_title = title
from prefixexempts as p
where a.title like p.text || '%';
