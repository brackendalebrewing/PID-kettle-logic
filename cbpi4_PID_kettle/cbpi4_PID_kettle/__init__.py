import asyncio
import logging
from cbpi.api import *
from pid import PID  # Import your custom PID controller

class PIDcontrol(CBPiKettleLogic):

    async def on_stop(self):
        await self.actor_off(self.heater)
        pass

    async def run(self):
        try:
            self.TEMP_UNIT = self.get_config_value("TEMP_UNIT", "C")
            wait_time = sampleTime = int(self.props.get("SampleTime", 5))
            boilthreshold = 98 if self.TEMP_UNIT == "C" else 208

            p = float(self.props.get("P", 117.0795))
            i = float(self.props.get("I", 0.2747))
            d = float(self.props.get("D", 41.58))
            maxout = int(self.props.get("Max_Output", 100))
            minout = int(self.props.get("Min_Output", 0))

            self.kettle = self.get_kettle(self.id)
            self.heater = self.kettle.heater
            heat_percent_old = maxout
            self.heater_actor = self.cbpi.actor.find_by_id(self.heater)

            await self.actor_on(self.heater, maxout)

            # Initialize your PID controller
            pid = PID(Kp=p, Ki=i, Kd=d, output_limits=(minout, maxout), sample_time=sampleTime)

            while self.running:
                current_kettle_power = self.heater_actor.power
                sensor_value = current_temp = self.get_sensor_value(self.kettle.sensor).get("value")
                target_temp = self.get_kettle_target_temp(self.id)

                heat_percent = pid(sensor_value)

                if (heat_percent_old != heat_percent) or (heat_percent != current_kettle_power):
                    await self.actor_set_power(self.heater, heat_percent)
                    heat_percent_old = heat_percent
                await asyncio.sleep(sampleTime)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logging.error(f"BM_PIDSmartBoilWithPump Error {e}")
        finally:
            self.running = False
            await self.actor_off(self.heater)

def setup(cbpi):
    cbpi.plugin.register("PIDcontrol", PIDcontrol)
