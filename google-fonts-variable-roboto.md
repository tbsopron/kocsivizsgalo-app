Examining how Google Fonts returns different [Roboto](https://fonts.google.com/specimen/Roboto?selection.family=Roboto) font files for various `User-Agent` strings. (h/t https://stackoverflow.com/a/27308229/93579)

The `src` URLs referenced below are what get served to the browsers when they access this font:

```html
<link href="https://fonts.googleapis.com/css?family=Roboto" rel="stylesheet">
```

This is referenced as part of [a Tweet](https://twitter.com/westonruter/status/1129420598541791233). For responding, please reply on Twitter as Gist comments send no notifications.

# Woff2 for Mac OS
```
curl -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36" https://fonts.googleapis.com/css?family=Roboto | grep 'src:' | head -n1
```
```css
src: local('Roboto'), local('Roboto-Regular'), url(https://fonts.gstatic.com/s/roboto/v19/KFOmCnqEu92Fr1Mu72xKKTU1Kvnz.woff2) format('woff2');
src: local('Roboto'), local('Roboto-Regular'), url(https://fonts.gstatic.com/s/roboto/v19/KFOmCnqEu92Fr1Mu5mxKKTU1Kvnz.woff2) format('woff2');
src: local('Roboto'), local('Roboto-Regular'), url(https://fonts.gstatic.com/s/roboto/v19/KFOmCnqEu92Fr1Mu7mxKKTU1Kvnz.woff2) format('woff2');
src: local('Roboto'), local('Roboto-Regular'), url(https://fonts.gstatic.com/s/roboto/v19/KFOmCnqEu92Fr1Mu4WxKKTU1Kvnz.woff2) format('woff2');
src: local('Roboto'), local('Roboto-Regular'), url(https://fonts.gstatic.com/s/roboto/v19/KFOmCnqEu92Fr1Mu7WxKKTU1Kvnz.woff2) format('woff2');
src: local('Roboto'), local('Roboto-Regular'), url(https://fonts.gstatic.com/s/roboto/v19/KFOmCnqEu92Fr1Mu7GxKKTU1Kvnz.woff2) format('woff2');
src: local('Roboto'), local('Roboto-Regular'), url(https://fonts.gstatic.com/s/roboto/v19/KFOmCnqEu92Fr1Mu4mxKKTU1Kg.woff2) format('woff2');
```

# Woff2 for Windows

```bash
curl -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36" https://fonts.googleapis.com/css?family=Roboto | grep 'src:'
```
```css
src: local('Roboto'), local('Roboto-Regular'), url(https://fonts.gstatic.com/s/roboto/v19/KFOmCnqEu92Fr1Mu72xKOzY.woff2) format('woff2');
src: local('Roboto'), local('Roboto-Regular'), url(https://fonts.gstatic.com/s/roboto/v19/KFOmCnqEu92Fr1Mu5mxKOzY.woff2) format('woff2');
src: local('Roboto'), local('Roboto-Regular'), url(https://fonts.gstatic.com/s/roboto/v19/KFOmCnqEu92Fr1Mu7mxKOzY.woff2) format('woff2');
src: local('Roboto'), local('Roboto-Regular'), url(https://fonts.gstatic.com/s/roboto/v19/KFOmCnqEu92Fr1Mu4WxKOzY.woff2) format('woff2');
src: local('Roboto'), local('Roboto-Regular'), url(https://fonts.gstatic.com/s/roboto/v19/KFOmCnqEu92Fr1Mu7WxKOzY.woff2) format('woff2');
src: local('Roboto'), local('Roboto-Regular'), url(https://fonts.gstatic.com/s/roboto/v19/KFOmCnqEu92Fr1Mu7GxKOzY.woff2) format('woff2');
src: local('Roboto'), local('Roboto-Regular'), url(https://fonts.gstatic.com/s/roboto/v19/KFOmCnqEu92Fr1Mu4mxK.woff2) format('woff2');
```

# Woff

```bash
curl -A "Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5355d Safari/8536.25" https://fonts.googleapis.com/css?family=Roboto | grep 'src:'
```
```css
src: local('Roboto'), local('Roboto-Regular'), url(https://fonts.gstatic.com/s/roboto/v19/KFOmCnqEu92Fr1Mu4mxMKTU1Kg.woff) format('woff');
```

# TrueType

```bash
curl -A "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; de-at) AppleWebKit/533.21.1 (KHTML, like Gecko) Version/5.0.5 Safari/533.21.1" https://fonts.googleapis.com/css?family=Roboto | grep 'src:'
```
```css
src: local('Roboto'), local('Roboto-Regular'), url(https://fonts.gstatic.com/s/roboto/v19/KFOmCnqEu92Fr1Mu4mxPKTU1Kg.ttf) format('truetype');
```

# SVG

```bash
curl -A "Mozilla/5.0 (iPhone; U; CPU like Mac OS X; en) AppleWebKit/420+ (KHTML, like Gecko) Version/3.0 Mobile/1A543 Safari/419.3" https://fonts.googleapis.com/css?family=Roboto | grep 'src:'
```
```css
src: local('Roboto'), local('Roboto-Regular'), url(https://fonts.gstatic.com/l/font?kit=KFOmCnqEu92Fr1Mu4mxN&skey=a0a0114a1dcab3ac&v=v19#Roboto) format('svg');
```

# EOT

```bash
curl -A "Mozilla/5.0 (Windows; U; MSIE 7.0; Windows NT 6.0; en-US)" https://fonts.googleapis.com/css?family=Roboto | grep 'src:'
```
```css
src: url(https://fonts.gstatic.com/s/roboto/v19/KFOmCnqEu92Fr1Mu4mxO.eot);
```