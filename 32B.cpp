#include <iostream>
#include<vector>
using namespace std;
int no1(string s){
    if(s==".")
    return 0;
    if(s=="-." )
    return 1;
    if(s=="--")
    return 2;
    return 0;
}
int main(){
    string s;
    cin>>s;
    vector<char> v;
    for(int i=0;i<s.size();i++){
        v.push_back(s[i]);
    }
    for(int i=0 ; i<v.size() ; i++){
        if(v[i]=='.' ){
            cout<<no1(string(1,v[i]));
        }
        else if(v[i]=='-'){
            if(v[i+1]=='.'){
                cout<<no1("-.") ;
                i++;
            }
            else if(v[i+1]=='-'){
                cout<<no1("--");
                i++;
            }
        }

   }
}