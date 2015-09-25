angular.module('telega', [])
.controller('TabsController', function($scope) {
    /* Init. */
    var self = this;
    self.tabs = pageInfo.tabs;
})
.controller('TableController', function($scope) {
    /* Init. */
    var self = this;
    self.rows = [];
    self.loading = true;
    self.columns = pageInfo.columns;

    rows = [{"name": "Nickelodeon", "button": "28", "link": "ntv+15"}];
    self.rows = angular.forEach(rows, function(row) {
        angular.forEach(row, function(value, column, row) {
            row[column] = {value: value, edit: false, sending: false};
        });
    });

    /* Functions. */
    self.openEditor = function(column, row) {
        if (column.editable) {
            row[column.name].edit = true;
        }
    };
    self.postChanges = function(column, row) {
        row[column.name].edit = false;
        row[column.name].sending = true;
    };
});
