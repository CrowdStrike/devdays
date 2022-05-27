FROM public.ecr.aws/ubuntu/ubuntu:18.04
RUN apt-get -yqq update
RUN apt-get -yqq install openjdk-8-jdk wget net-tools
RUN mkdir /opt/tomcat \
&& cd /opt/tomcat \
&& wget -q http://provisioning.aws.cs-labs.net/workshop/cwp/files/apache-tomcat-8.0.32.tar.gz -O apache-tomcat-8.0.32.tar.gz \
&& wget -q http://provisioning.aws.cs-labs.net/workshop/cwp/files/teds-web.xml -O teds-web.xml \
&& tar zxvf apache-tomcat-8.0.32.tar.gz \
&& cp teds-web.xml /opt/tomcat/apache-tomcat-8.0.32/conf/web.xml \
&& echo "export JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk-amd64" >> ~/.bashrc \
&& echo "export CATALINA_HOME=/opt/tomcat/apache-tomcat-8.0.32" >> ~/.bashrc
CMD ["/opt/tomcat/apache-tomcat-8.0.32/bin/catalina.sh", "run"]
EXPOSE 8080