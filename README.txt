I decided to not add a 'remember me' box.  By default, users will remained logged in for two weeks since the last time they visited the site.  Their cookie will refresh whenever they make a request.

Might be good to check the IP that their cookie is using.

I decided that it might be safer to use a 256-character string session token instead of storing an encrypted form of the username and password in the cookie.