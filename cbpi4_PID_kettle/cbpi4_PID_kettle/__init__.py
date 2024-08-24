import asyncio
import logging
from cbpi.api import *
from pid import PID  # Import your custom PID controller from pid.py

logger = logging.getLogger(__name__)

@parameters([
    Property.Number(label="P", configurable=True, description="P Value of PID"),
    Property.Number(label="I", configurable=True, description="I Value of PID"),
    Property.Number(label="D", configurable=True, description="D Value of PID"),
    Property.Select(label="SampleTime", options=[1,2,3,4,5], description="PID Sample time in seconds. Default: 5"),
    Property.Number(label="Max_Output", configurable=True, description="Maximum Power"),
    Property.Number(label="Min_Output", configurable=True, description="Minimum Power")
])
class PIDcontrol(CBPiKettleLogic):

    async def on_stop(self):
        await self.actor_off(self.heater)

    async def run(self):
        try:
            # Config and initial setup
            self.TEMP_UNIT = self.get_config_value("TEMP_UNIT", "C")
            sampleTime = int(self.props.get("SampleTime", 5))
            boilthreshold = 98 if self.TEMP_UNIT == "C" else 208

            # PID parameters
            p = float(self.props.get("P", 117.0795))
            i = float(self.props.get("I", 0.2747))
            d = float(self.props.get("D", 41.58))
            maxout = int(self.props.get("Max_Output", 255))
            minout = int(self.props.get("Min_Output", 0))

            # Actor and sensor setup
            self.kettle = self.get_kettle(self.id)
            self.heater = self.kettle.heater
            self.heater_actor = self.cbpi.actor.find_by_id(self.heater)
            heat_percent_old = maxout

            # Turn on the heater with maximum power at the start
            await self.actor_on(self.heater, maxout)

            # Initialize the PID controller
            pid = PID(Kp=p, Ki=i, Kd=d, output_limits=(minout, maxout), sample_time=sampleTime)

            while self.running:
                # Get current temperature and target temperature
                current_kettle_power = self.heater_actor.power
                sensor_value = current_temp = self.get_sensor_value(self.kettle.sensor).get("value")
                target_temp = self.get_kettle_target_temp(self.id)
                pid.setpoint = target_temp

                # Calculate new power output from PID
                heat_percent = pid(sensor_value)

                # Adjust heater power if necessary
                if (heat_percent_old != heat_percent) or (heat_percent != current_kettle_power):
                    await self.actor_set_power(self.heater, heat_percent)
                    heat_percent_old = heat_percent
                    
                logger.info(f"HEX PID Calculation: setpoint={pid.setpoint}")
                logger.info(f"HEX PID Constants: Kp={p}, Ki={i}, Kd={d}, Time Base={sampleTime}")
                logger.info(f"HEX PID Output: {heat_percent} (Output range: 0-{maxout})")    
                    

                # Wait for the next cycle
                await asyncio.sleep(sampleTime)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"PIDcontrol Error: {e}")
        finally:
            self.running = False
            await self.actor_off(self.heater)

def setup(cbpi):
    """
    This method is called by the server during startup.
    Here you need to register your plugins at the server.
    
    :param cbpi: the cbpi core 
    :return: 
    """
    cbpi.plugin.register("PIDcontrol", PIDcontrol)
