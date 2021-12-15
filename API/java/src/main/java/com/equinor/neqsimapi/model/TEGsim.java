package com.equinor.neqsimapi.model;

import com.equinor.neqsimapi.dto.TEGdehydrationRequest;
import neqsim.processSimulation.measurementDevice.HydrateEquilibriumTemperatureAnalyser;
import neqsim.processSimulation.measurementDevice.WaterDewPointAnalyser;
import neqsim.processSimulation.processEquipment.absorber.SimpleTEGAbsorber;
import neqsim.processSimulation.processEquipment.absorber.WaterStripperColumn;
import neqsim.processSimulation.processEquipment.distillation.DistillationColumn;
import neqsim.processSimulation.processEquipment.filter.Filter;
import neqsim.processSimulation.processEquipment.heatExchanger.HeatExchanger;
import neqsim.processSimulation.processEquipment.heatExchanger.Heater;
import neqsim.processSimulation.processEquipment.mixer.StaticMixer;
import neqsim.processSimulation.processEquipment.pump.Pump;
import neqsim.processSimulation.processEquipment.stream.Stream;
import neqsim.processSimulation.processEquipment.util.Calculator;
import neqsim.processSimulation.processEquipment.util.Recycle;
import neqsim.processSimulation.processEquipment.util.SetPoint;
import neqsim.processSimulation.processEquipment.util.StreamSaturatorUtil;
import neqsim.processSimulation.processEquipment.valve.ThrottlingValve;
import neqsim.processSimulation.processEquipment.separator.Separator;

public class TEGsim {

	public neqsim.processSimulation.processSystem.ProcessSystem getProcess(TEGdehydrationRequest req) {
		neqsim.thermo.system.SystemInterface feedGas = new neqsim.thermo.system.SystemSrkCPAstatoil(273.15 + 42.0,
				10.00);
		feedGas.addComponent("nitrogen", 0.245);
		feedGas.addComponent("CO2", 3.4);
		feedGas.addComponent("methane", 85.7);
		feedGas.addComponent("ethane", 5.981);
		feedGas.addComponent("propane", 2.743);
		feedGas.addComponent("i-butane", 0.37);
		feedGas.addComponent("n-butane", 0.77);
		feedGas.addComponent("i-pentane", 0.142);
		feedGas.addComponent("n-pentane", 0.166);
		feedGas.addComponent("n-hexane", 0.06);
		feedGas.addComponent("benzene", 0.01);
		feedGas.addComponent("water", 0.0);
		feedGas.addComponent("TEG", 0);
		feedGas.setMixingRule(10);
		feedGas.setMultiPhaseCheck(false);
		feedGas.init(0);
		feedGas.setMolarComposition(new double[] { req.liftGas_N2, req.liftGas_CO2, req.liftGas_Methane, req.liftGas_Ethane, req.liftGas_Propane, req.liftGas_iButane, req.liftGas_nButane, req.liftGas_iPentane, req.liftGas_nPentane, 0.0, 0.01, 0.0, 0.0});



		neqsim.thermo.system.SystemInterface coolingMedium = new neqsim.thermo.system.SystemSrkCPAstatoil(273.15 + 20.0, 10.00);
		coolingMedium.addComponent("water", 0.7, "kg/sec");
		coolingMedium.addComponent("MEG", 0.3, "kg/sec");
		coolingMedium.setMixingRule(10);
		coolingMedium.setMultiPhaseCheck(false);

		Stream coolingWater1 = new Stream("cooling water 1", coolingMedium);
		coolingWater1.setFlowRate(req.coolingMedium1FlowRate, "kg/hr");
		coolingWater1.setTemperature(req.coolingMedium1FeedTemperature, "C");
		coolingWater1.setPressure(req.coolingMedium1FeedPressure, "bara");

		Stream dryFeedGas = new Stream("dry feed gas", feedGas);
		dryFeedGas.setFlowRate(req.feedGasFlowRate, "MSm3/day");
		dryFeedGas.setTemperature(req.feedGasTemperature, "C");
		dryFeedGas.setPressure(req.feedGasPressure, "bara");

		StreamSaturatorUtil saturatedFeedGas = new StreamSaturatorUtil(dryFeedGas);
		saturatedFeedGas.setName("water saturator");

		Stream waterSaturatedFeedGas = new Stream(saturatedFeedGas.getOutStream());
		waterSaturatedFeedGas.setName("water saturated feed gas");

		HydrateEquilibriumTemperatureAnalyser hydrateTAnalyser = new HydrateEquilibriumTemperatureAnalyser(
				waterSaturatedFeedGas);
		hydrateTAnalyser.setName("hydrate temperature analyser");

		neqsim.thermo.system.SystemInterface feedTEG = (neqsim.thermo.system.SystemInterface) feedGas.clone();
		feedTEG.setMolarComposition(new double[] { 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.03, 0.97 });

		Heater feedTPsetterToAbsorber = new Heater("TP of gas to absorber", waterSaturatedFeedGas);
		feedTPsetterToAbsorber.setOutPressure(req.absorberFeedGasPressure, "bara");
		feedTPsetterToAbsorber.setOutTemperature(req.absorberFeedGasTemperature, "C");

		Stream feedToAbsorber = new Stream(feedTPsetterToAbsorber.getOutStream());
		feedToAbsorber.setName("feed to TEG absorber");

		HydrateEquilibriumTemperatureAnalyser hydrateTAnalyser2 = new HydrateEquilibriumTemperatureAnalyser(feedToAbsorber);
		hydrateTAnalyser2.setName("hydrate temperature gas to absorber");

		WaterDewPointAnalyser waterDewPointAnalyserToAbsorber = new WaterDewPointAnalyser(feedToAbsorber);
		waterDewPointAnalyserToAbsorber.setMethod("multiphase");
		waterDewPointAnalyserToAbsorber.setReferencePressure(req.absorberFeedGasPressure);
		waterDewPointAnalyserToAbsorber.setName("water dew point gas to absorber");

		Stream TEGFeed = new Stream("lean TEG to absorber", feedTEG);
		TEGFeed.setFlowRate(req.leanTEGFlowRate, "kg/hr");
		TEGFeed.setTemperature(req.leanTEGTemperature, "C");
		TEGFeed.setPressure(req.absorberFeedGasPressure, "bara");


		SimpleTEGAbsorber absorber = new SimpleTEGAbsorber();
		absorber.setName("TEG absorber");
		absorber.addGasInStream(feedToAbsorber);
		absorber.addSolventInStream(TEGFeed);
		absorber.setNumberOfStages(req.numberOfStagesTEGabsorber);
		absorber.setStageEfficiency(req.stageEfficiencyTEGabsorber);
		absorber.setInternalDiameter(2.240);

		Stream dehydratedGas = new Stream(absorber.getGasOutStream());
		dehydratedGas.setName("dry gas from absorber");

		Stream richTEG = new Stream(absorber.getLiquidOutStream());
		richTEG.setName("rich TEG from absorber");

		HydrateEquilibriumTemperatureAnalyser waterDewPointAnalyser = new HydrateEquilibriumTemperatureAnalyser(
				dehydratedGas);
		waterDewPointAnalyser.setReferencePressure(70.0);
		waterDewPointAnalyser.setName("hydrate dew point analyser");

		WaterDewPointAnalyser waterDewPointAnalyser2 = new WaterDewPointAnalyser(dehydratedGas);
		waterDewPointAnalyser2.setReferencePressure(70.0);
		waterDewPointAnalyser2.setName("water dew point analyser");

		ThrottlingValve glycol_flash_valve = new ThrottlingValve("Flash valve", richTEG);
		glycol_flash_valve.setName("Rich TEG HP flash valve");
		glycol_flash_valve.setOutletPressure(req.flashDrumPressure);

		Heater richGLycolHeaterCondenser = new Heater(glycol_flash_valve.getOutStream());
		richGLycolHeaterCondenser.setName("rich TEG preheater");

		HeatExchanger heatEx2 = new HeatExchanger(richGLycolHeaterCondenser.getOutStream());
		heatEx2.setName("rich TEG heat exchanger 1");
		heatEx2.setGuessOutTemperature(273.15 + 62.0);
		heatEx2.setUAvalue(req.UAvalueLeanRichTEGHeatExchanger2);

		Separator flashSep = new Separator(heatEx2.getOutStream(0));
		flashSep.setName("degasing separator");
		flashSep.setInternalDiameter(1.2);

		Stream flashGas = new Stream(flashSep.getGasOutStream());
		flashGas.setName("gas from degasing separator");

		Stream flashLiquid = new Stream(flashSep.getLiquidOutStream());
		flashLiquid.setName("liquid from degasing separator");

		Filter filter = new Filter(flashLiquid);
		filter.setName("TEG fine filter");
		filter.setDeltaP(req.finefilterdeltaP, "bara");

		HeatExchanger heatEx = new HeatExchanger(filter.getOutStream());
		heatEx.setName("lean/rich TEG heat-exchanger");
		heatEx.setGuessOutTemperature(273.15 + 130.0);
		heatEx.setUAvalue(req.UAvalueLeanRichTEGHeatExchanger);

		ThrottlingValve glycol_flash_valve2 = new ThrottlingValve("LP flash valve", heatEx.getOutStream(0));
		glycol_flash_valve2.setName("Rich TEG LP flash valve");
		glycol_flash_valve2.setOutletPressure(req.reboilerPressure);

		neqsim.thermo.system.SystemInterface stripGas = (neqsim.thermo.system.SystemInterface) feedGas.clone();

		Stream strippingGas = new Stream("stripGas", stripGas);
		strippingGas.setFlowRate(req.strippingGasRate, "Sm3/hr");
		strippingGas.setTemperature(req.strippingGasFeedTemperature, "C");
		strippingGas.setPressure(req.reboilerPressure, "bara");

		Stream gasToReboiler = (Stream) strippingGas.clone();
		gasToReboiler.setName("gas to reboiler");

		DistillationColumn column = new DistillationColumn(1, true, true);
		column.setName("TEG regeneration column");
		column.addFeedStream(glycol_flash_valve2.getOutStream(), 1);
		column.getReboiler().setOutTemperature(273.15 + req.reboilerTemperature);
		column.getCondenser().setOutTemperature(273.15 + req.condenserTemperature);
		column.getTray(1).addStream(gasToReboiler);
		column.setTopPressure(req.condenserPressure);
		column.setBottomPressure(req.reboilerPressure);
		column.setInternalDiameter(0.56);
		
		Heater coolerRegenGas = new Heater(column.getGasOutStream());
		coolerRegenGas.setName("regen gas cooler");
		coolerRegenGas.setOutTemperature(273.15 + req.regenerationGasCoolerTemperature);

		HeatExchanger overheadCondHX = new HeatExchanger(column.getGasOutStream());
		overheadCondHX.setName("overhead condenser heat-exchanger");
		overheadCondHX.setGuessOutTemperature(273.15 + 50.0);
		overheadCondHX.setUAvalue(req.UAoverheadCondenser);
		overheadCondHX.setFeedStream(1, coolingWater1);

		Separator sepregenGas = new Separator(coolerRegenGas.getOutStream());
		sepregenGas.setName("regen gas separator");

		Stream gasToFlare = new Stream(sepregenGas.getGasOutStream());
		gasToFlare.setName("gas to flare");

		Stream liquidToTrreatment = new Stream(sepregenGas.getLiquidOutStream());
		liquidToTrreatment.setName("water to treatment");

		WaterStripperColumn stripper = new WaterStripperColumn("TEG stripper");
		stripper.addSolventInStream(column.getLiquidOutStream());
		stripper.addGasInStream(strippingGas);
		stripper.setNumberOfStages(req.numberOfStagesStripper);
		stripper.setStageEfficiency(req.stageEfficiencyStripper);

		Recycle recycleGasFromStripper = new Recycle("stripping gas recirc");
		recycleGasFromStripper.addStream(stripper.getGasOutStream());
		recycleGasFromStripper.setOutletStream(gasToReboiler);

		heatEx.setFeedStream(1, stripper.getLiquidOutStream());

		Heater bufferTank = new Heater("TEG buffer tank", heatEx.getOutStream(1));
		bufferTank.setOutTemperature(273.15 + req.bufferTankTemperatureTEG);

		Pump hotLeanTEGPump = new Pump(bufferTank.getOutStream());
		hotLeanTEGPump.setName("lean TEG LP pump");
		hotLeanTEGPump.setOutletPressure(req.hotTEGpumpPressure);
		hotLeanTEGPump.setIsentropicEfficiency(req.TEGpumpIsentropicEfficiency);

		heatEx2.setFeedStream(1, hotLeanTEGPump.getOutStream());

		Heater coolerhOTteg3 = new Heater(heatEx2.getOutStream(1));
		coolerhOTteg3.setName("lean TEG cooler");
		coolerhOTteg3.setOutTemperature(273.15 + req.leanTEGTemperature);

		Pump hotLeanTEGPump2 = new Pump(coolerhOTteg3.getOutStream());
		hotLeanTEGPump2.setName("lean TEG HP pump");
		hotLeanTEGPump2.setOutletPressure(req.absorberFeedGasPressure);
		hotLeanTEGPump2.setIsentropicEfficiency(req.TEGpumpIsentropicEfficiency);

		SetPoint pumpHPPresSet = new SetPoint("HP pump set", hotLeanTEGPump2, "pressure", feedToAbsorber);

		Stream leanTEGtoabs = new Stream(hotLeanTEGPump2.getOutStream());
		leanTEGtoabs.setName("lean TEG to absorber");

		neqsim.thermo.system.SystemInterface pureTEG = (neqsim.thermo.system.SystemInterface) feedGas.clone();
		pureTEG.setMolarComposition(new double[] { 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0 });

		Stream makeupTEG = new Stream("makeup TEG", pureTEG);
		makeupTEG.setFlowRate(1e-6, "kg/hr");
		makeupTEG.setTemperature(req.leanTEGTemperature, "C");
		makeupTEG.setPressure(req.absorberFeedGasPressure, "bara");

		Calculator makeupCalculator = new Calculator("TEG makeup calculator");
		makeupCalculator.addInputVariable(dehydratedGas);
		makeupCalculator.addInputVariable(flashGas);
		makeupCalculator.addInputVariable(gasToFlare);
		makeupCalculator.addInputVariable(liquidToTrreatment);
		makeupCalculator.setOutputVariable(makeupTEG);

		StaticMixer makeupMixer = new StaticMixer("makeup mixer");
		makeupMixer.addStream(leanTEGtoabs);
		makeupMixer.addStream(makeupTEG);

		Recycle resycleLeanTEG = new Recycle("lean TEG resycle");
		resycleLeanTEG.addStream(makeupMixer.getOutStream());
		resycleLeanTEG.setOutletStream(TEGFeed);
		resycleLeanTEG.setPriority(200);
		resycleLeanTEG.setDownstreamProperty("flow rate");

		richGLycolHeaterCondenser.setEnergyStream(column.getCondenser().getEnergyStream());

		neqsim.processSimulation.processSystem.ProcessSystem operations = new neqsim.processSimulation.processSystem.ProcessSystem();
		operations.add(coolingWater1);
		operations.add(dryFeedGas);
		operations.add(saturatedFeedGas);
		operations.add(waterSaturatedFeedGas);
		operations.add(hydrateTAnalyser);
		operations.add(feedTPsetterToAbsorber);
		operations.add(feedToAbsorber);
		operations.add(hydrateTAnalyser2);
		operations.add(waterDewPointAnalyserToAbsorber);
		operations.add(TEGFeed);
		operations.add(absorber);
		operations.add(dehydratedGas);
		operations.add(waterDewPointAnalyser);
		operations.add(waterDewPointAnalyser2);
		operations.add(richTEG);
		operations.add(glycol_flash_valve);
		operations.add(richGLycolHeaterCondenser);
		operations.add(heatEx2);
		operations.add(flashSep);
		operations.add(flashGas);
		operations.add(flashLiquid);
		operations.add(filter);
		operations.add(heatEx);
		operations.add(glycol_flash_valve2);
		operations.add(gasToReboiler);
		operations.add(column);
		operations.add(coolerRegenGas);
		operations.add(overheadCondHX);
		operations.add(sepregenGas);
		operations.add(gasToFlare);
		operations.add(liquidToTrreatment);
		operations.add(strippingGas);
		operations.add(stripper);
		operations.add(recycleGasFromStripper);
		operations.add(bufferTank);
		operations.add(hotLeanTEGPump);
		operations.add(coolerhOTteg3);
		operations.add(hotLeanTEGPump2);
		operations.add(pumpHPPresSet);
		operations.add(leanTEGtoabs);
		operations.add(makeupCalculator);
		operations.add(makeupTEG);
		operations.add(makeupMixer);
		operations.add(resycleLeanTEG);
		return operations;
	}

}