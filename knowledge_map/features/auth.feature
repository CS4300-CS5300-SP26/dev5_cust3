Feature: User Authentication

    Scenario: A new user registers successfully
        Given I am on the registration page
        When I register with username "newuser" and password "test"
        Then I should be redirected to the movies page
        And I should be logged in

    Scenario: A user registers with a duplicate username
        Given a user already exists with username "existing" and password "pass1234"
        And I am on the registration page
        When I register with username "existing" and password "test"
        Then I should see "An error occurred"

    Scenario: A user logs in successfully
        Given a user already exists with username "test" and password "test"
        And I am on the login page
        When I login with username "test" and password "test"
        Then I should be redirected to the movies page
        And I should be logged in

    Scenario: A user logs in with wrong password
        Given a user already exists with username "test" and password "test"
        And I am on the login page
        When I login with username "test" and password "wrongpass"
        Then I should see "Invalid username or password"

    Scenario: A logged in user logs out
        Given I am logged in as "test" with password "test"
        When I log out
        Then I should be redirected to the movies page
        And I should not be logged in