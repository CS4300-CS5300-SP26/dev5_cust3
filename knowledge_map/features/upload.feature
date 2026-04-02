Feature: Upload Content

  Scenario: User navigates to upload page from navbar
    Given I am on the home page
    When I click Upload Content in the sidebar
    Then I should be taken to the upload page

  Scenario: User uploads a PDF file
    Given I am on the upload page
    When I select a PDF file and click Upload
    Then the file should be saved and visible in the uploaded files list

  Scenario: User views previously uploaded files
    Given I am on the upload page
    When I have uploaded files in the past
    Then I should see a list of all previously uploaded files

  Scenario: User deletes an uploaded file
    Given I am on the upload page
    And there is at least one file in the list
    When I click Delete on a file
    Then the file should be removed from the list and deleted from storage