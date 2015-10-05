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

    var path = location.pathname.replace(/^\/([^/]*).*$/, '$1');
    angular.forEach(self.tabs, function (tab) {
        tab._current = (tab.link == path);
    });
})
.controller('LogmonController', function ($http, $log) {
    /* Init. */
    var self = this;
    self.count = 0;
    self.apiPath = '/api/logmon/';

    $http.get(self.apiPath).then(
        function (response) {
            self.count = +response.data;
        },
        function (response) {
            noticeApiError($log, self.apiPath, response);
        }
    );

    /* Functions. */
    self.resetTime = function () {
        $http.post(self.apiPath).then(
            function(response) {
                self.count = 0;
            },
            function(response) {
                noticeApiError($log, self.apiPath, response);
            }
        );
    };
})
.controller('TableController', function ($http, $log) {
    /* Init. */
    var self = this;
    self.rows = [];
    self.loading = true;
    self.editable = false;
    self.columns = pageInfo.columns;
    self.apiPath = '/api' + location.pathname;
    self.newRowForm = {
        opened: false,
        sending: false,
        object: {},
    };

    angular.forEach(self.columns, function(column) {
        if (column.editable) {
            self.editable = true;
        }
    });
    setTimeout(function () {
        self.loadRows();
    }, 0);

    /* Functions. */
    self.loadRows = function () {
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
    }
    self.openCellEditor = function (column, row) {
        if (column.editable) {
            row[column.name].oldValue = row[column.name].value;
            row[column.name].edit = true;
        }
    };
    self.applyChanges = function (form, column, row) {
        if (form.$invalid) {
            return;
        }
        row[column.name].edit = false;
        row[column.name].sending = true;
        $http.put(self.apiPath + row.id, {
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
    self.openAddRowForm = function () {
        self.newRowForm.object = {};
        self.newRowForm.opened = true;
    };
    self.closeAddRowForm = function () {
        self.newRowForm.opened = false;
    };
    self.addRow = function () {
        self.newRowForm.sending = true;
        $http.post(self.apiPath, self.newRowForm.object).then(
            function(response) {
                self.newRowForm.opened = false;
                self.newRowForm.sending = false;
                self.loadRows();
            },
            function(response) {
                noticeApiError($log, self.apiPath, response);
            }
        );
    };
    self.deleteRow = function (row) {
        $http.delete(self.apiPath + row.id).then(
            function(response) {
                var index = 0;
                self.rows.splice(row._index-1, 1);
                angular.forEach(self.rows, function(row) {
                    row._index = ++index;
                });
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
