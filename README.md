# Early Access to CYROCK libraries

## Installation, see also [pom.xml](./pom.xml)

First, add your GitHub credentials to the settings.xml.

More info can be found in the official [GitHub documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-apache-maven-registry#installing-a-package).

```xml
<servers>
    <server>
        <id>cyrock-early-access</id>
        <username>your-github-username</username>
        <password>your-personal-access-token</password>
    </server>
</servers>
```

Add the following repository.

```xml
<repositories>
    <repository>
        <id>cyrock-early-access</id>
        <name>GitHub CYROCK Early Access Packages</name>
        <url>https://maven.pkg.github.com/cyrock-ai/early-access</url>
    </repository>
</repositories>
```

Now you can use the [CYROCK packages](https://github.com/orgs/cyrock-ai/packages?repo_name=early-access):

---

[<img src="vectralink/etc/vectralink-logo-with-text.svg" alt="Vectralink Logo" width="500" />](vectralink/README.md)
