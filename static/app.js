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

    var path = location.pathname.slice(1);
    angular.forEach(self.tabs, function (tab) {
        tab._current = (tab.link == path);
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
            var index = 0;
            self.rows = angular.forEach(response.data, function(row) {
                angular.forEach(row, function(value, column, row) {
                    if (column != 'id' && column[0] != '_') {
                        row[column] = {value: value, edit: false, sending: false};
                    }
                });
                row._highlighted = (row.id == pageInfo.hl);
                row._index = ++index;
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
            row[column.name].oldValue = row[column.name].value;
            row[column.name].edit = true;
        }
    };
    self.postChanges = function (form, column, row) {
        if (form.$invalid) {
            return;
        }
        row[column.name].edit = false;
        row[column.name].sending = true;
        $http.post(self.apiPath, {
            id: row.id,
            field: column.name,
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
    self.catchEscape = function ($event, column, row) {
        if ($event.keyCode == 27) {
            row[column.name].value = row[column.name].oldValue;
            row[column.name].edit = false;
        }
    };
});
