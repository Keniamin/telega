function noticeApiError($log, path, response) {
    $log.warn(
        'Failed to ' + response.config.method + ' data ' + path + '\n' +
        'Reason: ' + response.statusText
    );
}

angular.module('telega', [])
.controller('TabsController', function () {
    /* Init. */
    var self = this;
    self.tabs = pageInfo.tabs;

    path = location.pathname;
    angular.forEach(self.tabs, function (tab) {
        tab.active = (tab.link == path);
    });
})
.controller('TableController', function ($http, $log) {
    /* Init. */
    var self = this;
    self.rows = [];
    self.loading = true;
    self.columns = pageInfo.columns;

    self.apiPath = '/api' + location.pathname;
    $http.get(self.apiPath).then(
        function (response) {
            self.rows = angular.forEach(response.data, function(row) {
                angular.forEach(row, function(value, column, row) {
                    row[column] = {value: value, edit: false, sending: false};
                });
            });
            self.loading = false;
        },
        function (response) {
            noticeApiError($log, self.apiPath, response);
        }
    );

    /* Functions. */
    self.openEditor = function (column, row) {
        if (column.editable) {
            row[column.name].edit = true;
        }
    };
    self.postChanges = function (column, row) {
        row[column.name].edit = false;
        row[column.name].sending = true;
        $http.post(self.apiPath, {
            id: row.id,
            value: row[column.name].value,
        }).then(
            function(response) {
                row[column.name].sending = false;
            },
            function(response) {
                noticeApiError($log, self.apiPath, response);
            }
        );
    };
});
