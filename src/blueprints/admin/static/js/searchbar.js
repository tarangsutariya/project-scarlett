let requestsearch = document.getElementById("requestsearch")
function request_search(){
   
    let requestsearch = document.getElementById("requestsearch")
    let requesttable = document.getElementById("userrequests")
    let hiddencount = 0;
    for(let i = 0,row;row=requesttable.rows[i];i++){
        if(i==0 ||i==1|| i==requesttable.rows.length-1) continue;
        
        if(requestsearch.value.length>0 && requestsearch.value[0]=='#' && !(row.cells[0].innerText).includes(requestsearch.value.slice(1))){
        hiddencount+=1;
        row.style.display="None"
        }else if(!(requestsearch.value.length>0 && requestsearch.value[0]=='#')&&!(row.cells[1].innerText).includes(requestsearch.value) && !(row.cells[2].innerText).includes(requestsearch.value)){
            hiddencount+=1;
            row.style.display="None"   
        }
        else{
            row.style.display=""
        }
    }
   if(hiddencount==requesttable.rows.length-3){
    requesttable.rows[1].style.display="";
   }else{
    requesttable.rows[1].style.display="None"
   }

}

