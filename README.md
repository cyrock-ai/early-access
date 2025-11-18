# Early Access to CYROCK libraries

## Installation (see pom.xml)

First, add the GitHub credentials to your settings.xml.

```xml
<servers>
    <server>
        <id>cyrock-early-access</id>
        <username>your-github-username</username>
        <password>your-personal-access-token</password>
    </server>
</servers>
```

Add following repository.

```xml
<repositories>
    <repository>
        <id>cyrock-early-access</id>
        <name>GitHub CYROCK Early Access Packages</name>
        <url>https://maven.pkg.github.com/cyrock-ai/early-access</url>
    </repository>
</repositories>
```

Now you can use the CYROCK libraries.
