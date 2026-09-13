// TED2 native worker. Private stdio protocol, never a network listener.
// SQLite binds are positional; no shell interpolation. Transactions persist
// across requests on this process. PHP/PDO remains the default adapter.
#include <sqlite3.h>
#include <json-c/json.h>
#include <algorithm>
#include <cctype>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
static json_object* get(json_object* p,const char* k){json_object* v=nullptr;json_object_object_get_ex(p,k,&v);return v;}
static std::string text(json_object* p){return p?json_object_get_string(p):"";}
static std::string lower(std::string s){for(char &c:s)c=static_cast<char>(std::tolower(static_cast<unsigned char>(c)));return s;}
int main(int argc,char**argv){
 sqlite3* db=nullptr; bool rank=argc==2 && std::string(argv[1])=="--rank";
 if(argc!=2){std::cerr<<"Usage: ted2-worker database | --rank\n";return 2;}
 if(!rank && sqlite3_open_v2(argv[1],&db,SQLITE_OPEN_READWRITE|SQLITE_OPEN_CREATE,nullptr)!=SQLITE_OK){std::cerr<<"Database unavailable\n";return 2;}
 if(db){sqlite3_busy_timeout(db,15000);sqlite3_exec(db,"PRAGMA foreign_keys=ON",nullptr,nullptr,nullptr);}
 std::string line;
 while(std::getline(std::cin,line)){
  json_object* result=json_object_new_object();json_object* req=nullptr;
  try{
   if(line.size()>4*1024*1024)throw std::runtime_error("Frame too large");
   req=json_tokener_parse(line.c_str());if(!req||json_object_get_type(req)!=json_type_object)throw std::runtime_error("Invalid protocol frame");
   json_object* rows=json_object_new_array();json_object_object_add(result,"rows",rows);
   if(rank){
    auto docs=get(req,"documents"),terms=get(req,"terms");
    if(!docs||!terms||json_object_get_type(docs)!=json_type_array||json_object_get_type(terms)!=json_type_array)throw std::runtime_error("Invalid ranking input");
    for(size_t i=0;i<json_object_array_length(docs);++i){auto doc=json_object_array_get_idx(docs,i);int score=0;std::string hay=lower(text(get(doc,"title")));for(size_t j=0;j<json_object_array_length(terms);++j){auto term=lower(text(json_object_array_get_idx(terms,j)));if(!term.empty()&&hay.find(term)!=std::string::npos)++score;}
     auto row=json_object_new_object();json_object_object_add(row,"id",json_object_new_string(text(get(doc,"id")).c_str()));json_object_object_add(row,"score",json_object_new_int(score));json_object_array_add(rows,row);
    }
   }else{
    auto sql=text(get(req,"sql"));auto params=get(req,"params");if(sql.empty()||!params||json_object_get_type(params)!=json_type_array)throw std::runtime_error("Invalid query");
    sqlite3_stmt* raw=nullptr;const char* tail=nullptr;
    if(sqlite3_prepare_v2(db,sql.c_str(),static_cast<int>(sql.size()),&raw,&tail)!=SQLITE_OK)throw std::runtime_error(sqlite3_errmsg(db));
    std::unique_ptr<sqlite3_stmt,decltype(&sqlite3_finalize)> stmt(raw,sqlite3_finalize);
    while(tail&&*tail&&std::isspace(static_cast<unsigned char>(*tail)))++tail;
    if(tail&&*tail)throw std::runtime_error("One statement per frame");
    if(!raw||sqlite3_bind_parameter_count(raw)!=static_cast<int>(json_object_array_length(params)))throw std::runtime_error("Parameter count mismatch");
    for(size_t i=0;i<json_object_array_length(params);++i){auto v=json_object_array_get_idx(params,i);int k=static_cast<int>(i+1);switch(json_object_get_type(v)){
     case json_type_null:sqlite3_bind_null(raw,k);break;
     case json_type_int:case json_type_boolean:sqlite3_bind_int64(raw,k,json_object_get_int64(v));break;
     case json_type_double:sqlite3_bind_double(raw,k,json_object_get_double(v));break;
     case json_type_string:sqlite3_bind_text(raw,k,json_object_get_string(v),json_object_get_string_len(v),SQLITE_TRANSIENT);break;
     default:throw std::runtime_error("Unsupported parameter");}
    }
    int rc;while((rc=sqlite3_step(raw))==SQLITE_ROW){auto row=json_object_new_object();for(int c=0;c<sqlite3_column_count(raw);++c){json_object* val=nullptr;switch(sqlite3_column_type(raw,c)){case SQLITE_NULL:break;case SQLITE_INTEGER:val=json_object_new_int64(sqlite3_column_int64(raw,c));break;case SQLITE_FLOAT:val=json_object_new_double(sqlite3_column_double(raw,c));break;default:val=json_object_new_string_len(reinterpret_cast<const char*>(sqlite3_column_text(raw,c)),sqlite3_column_bytes(raw,c));break;}json_object_object_add(row,sqlite3_column_name(raw,c),val);}json_object_array_add(rows,row);}
    if(rc!=SQLITE_DONE) throw std::runtime_error(sqlite3_errmsg(db));
    json_object_object_add(result,"changes",json_object_new_int(sqlite3_changes(db)));
   }
   json_object_object_add(result,"ok",json_object_new_boolean(true));
  }catch(const std::exception&e){json_object_object_add(result,"ok",json_object_new_boolean(false));json_object_object_add(result,"error",json_object_new_string(e.what()));}
  std::cout<<json_object_to_json_string_ext(result,JSON_C_TO_STRING_PLAIN)<<'\n'<<std::flush;if(req)json_object_put(req);json_object_put(result);
 }
 if(db) sqlite3_close(db);
 return 0;
}
