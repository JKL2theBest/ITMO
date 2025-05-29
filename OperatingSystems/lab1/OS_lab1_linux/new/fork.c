#include<stdio.h>
#include<unistd.h> //for fork
#include<stdlib.h> //for system

int main(){
while(1){
fork();
system("ps -e | wc -l >> log.txt");
}
return 0;
}
