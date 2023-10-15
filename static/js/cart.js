const updateBtns = document.getElementsByClassName('update-cart')
const cartTotal = document.querySelector('#cart-total');


for(let i = 0; i < updateBtns.length; i++){
    updateBtns[i].addEventListener('click', function(){
        const productId = this.dataset.product
        const action = this.dataset.action
        console.log('productId:',productId, 'Action:',action)

        if(user === 'AnonymousUser'){
            addCookieItem(productId, action)
        }else{
            addToCartV2(productId)
            console.log("added to cart v2")
        }
    })
}

function addCookieItem(productId, action){
    console.log('Not logged in..')

    if(action === 'add'){
        if(!cart[productId]){
            cart[productId] = {'quantity':1}
        }else{
            cart[productId]['quantity'] += 1
        }
    }

    if(action === 'remove'){
        cart[productId]['quantity'] -= 1

        if(cart[productId]['quantity'] <= 0){
            console.log('Remove Item')
            delete cart[productId]
        }
    }


    console.log('Cart:>>>>', cart)

    cartTotal.innerText = Object.keys(cart).length;

    document.cookie = 'cart=' + JSON.stringify(cart) + ";domain=;path=/";
}



function addToCartV2(itemId) {
    fetch(`/add-to-cart/${itemId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({}),
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}