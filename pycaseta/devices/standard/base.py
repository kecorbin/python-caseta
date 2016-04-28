import time
import logging

logging.getLogger(__name__)

def is_desired_state_reached(caseta_device_state):
    """
    :type caseta_device_state: dict
    """
    # TODO  assume that desired state was reached for now
    # desired_state = caseta_device_state.get('desired_state', {})
    # for name, value in desired_state.items():
    #     if value != caseta_device_state.get(name):
    #         return False

    return True


class CasetaBinarySwitch(object):
    """
    json_obj holds the json stat at init (if there is a refresh it's updated)
    it's the native format for this objects methods
    """

    def __init__(self, device_state_as_json, api_interface, object_prefix=None):
        """
        :type api_interface pycaseta.api.WinkApiInterface:
        :return:
        """
        self.api_interface = api_interface
        self.objectprefix = object_prefix
        self.json_state = device_state_as_json
        self._last_call = (0, None)

    def __str__(self):
        return "%s %s %s" % (self.name(), self.device_id(), self.state())

    def __repr__(self):
        return "<Caseta switch %s %s %s>" % (self.name(),
                                             self.device_id(), self.state())

    @property
    def _last_reading(self):
        return {}

    def name(self):
        return self.json_state.get('Name', "Unknown Name")

    @property
    def available(self):
        #TODO currently assuming that the light is available

        return True

    def _update_state_from_response(self, response_json, require_desired_state_fulfilled=False):
        """
        :param response_json: the json obj returned from query
        """
        self.json_state['state']['output'] = response_json['state']['output']

    def state(self):
        # Optimistic approach to setState:
        # Within 15 seconds of a call to setState we assume it worked.
        val = self.json_state['state']['output']
        return float(val) > 0

    def update_state(self, require_desired_state_fulfilled=False):
        """ Update state with latest info from Wink API. """
        response = self.api_interface.get_device_state(self)
        self._update_state_from_response(response, require_desired_state_fulfilled)

    def device_id(self):
        return self.json_state.get('ID', self.name())

    def set_state(self, state, **kwargs):
        """
        :param state:   a boolean of true (on) or false ('off')
        :return: nothing
        """
        response = self.api_interface.set_device_state(self, state)
        logging.info('Set_state Got Response: {}'.format(response))
        self._update_state_from_response(response)
        self._last_call = (time.time(), state)

    def wait_till_desired_reached(self):
        """ Wait till desired state reached. Max 10s. """
        # TODO: Get rid of this.  Busy-wait loops can go in whatever project is making use of this library.
        if self._recent_state_set():
            return

        # self.refresh_state_at_hub()
        tries = 1

        while True:
            self.update_state()
            last_read = self._last_reading

            if last_read.get('desired_powered') == last_read.get('powered') or tries == 5:
                break

            time.sleep(2)

            tries += 1
            self.update_state()
            last_read = self._last_reading

    def _recent_state_set(self):
        return time.time() - self._last_call[0] < 15


def build_device(device_state_as_json, api_interface):
    """
    Builds caseta devices based on json values from integration report
    :param device_state_as_json:
    :param api_interface:
    :return:
    """
    new_object = CasetaBinarySwitch(device_state_as_json, api_interface, object_prefix="light_bulb")
    return new_object or CasetaBinarySwitch(device_state_as_json, api_interface)
