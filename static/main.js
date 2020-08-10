updateList = function(directory) {
    const input = document.getElementById(directory);
    const output = document.getElementById(directory + '_files');
    let list = "";
    for (let i = 0; i < input.files.length; ++i) {
        list += '<li>' + input.files.item(i).name + '</li>';
    }
    output.innerHTML = '<ul>'+ list +'</ul>';
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelector('#form').onsubmit = () => {

        const request = new XMLHttpRequest();
        const directory_a = document.getElementById('directory_a');
        const directory_b = document.getElementById('directory_b');
        const match = document.querySelector('#match').value;
        request.open('POST', '/process');

        request.onload = () => {
            const data = JSON.parse(request.responseText);
            if (data.success == true) {
                let scores = '';
                for (let i = 0; i < data.result.length; ++i) {
                    scores += '<li>' + data.result[i] + '</li>';
                }
                document.getElementById('result').innerHTML = '<ul>' + scores + '</ul>';
            }
            else {
                document.getElementById('result').innerHTML = data.result;
            }

        }

        const data = new FormData();
        Array.from(directory_a.files).forEach((file) => {
            data.append('directory_a[]', file)
        })
        Array.from(directory_b.files).forEach((file) => {
            data.append('directory_b[]', file)
        })
        data.append('match', match)

        request.send(data)
        return false
    }
})